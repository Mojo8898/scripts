#!/usr/bin/env python3

import argparse
import base64
import hashlib
import hmac
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)
VERBOSE = False

BANNER = r"""
  ____  _   _  ____ _____   _   _       _                 _
 | __ )| | | |/ ___| ____| | | | |_ __ | | ___   __ _  __| | ___ _ __
 |  _ \| |_| | |   |  _|   | | | | '_ \| |/ _ \ / _` |/ _` |/ _ \ '__|
 | |_) |  _  | |___| |___  | |_| | |_) | | (_) | (_| | (_| |  __/ |
 |____/|_| |_|\____|_____|  \___/| .__/|_|\___/ \__,_|\__,_|\___|_|
                                  |_|
"""


def banner():
    print(BANNER)


def vlog(*args, **kwargs):
    """Print only when verbose mode is enabled."""
    if VERBOSE:
        print("[VERBOSE]", *args, **kwargs)


def query_bloodhound_api(uri: str, method: str, creds: dict,
                         body_file_name: str = "", body_json: dict = None) -> dict:
    """Sign and execute a BloodHound API request.

    body_file_name: path to a file to send as the body (zip or json file)
    body_json:      a dict to serialize and send as a JSON body
    """

    # Step 1: HMAC over method + uri
    digester = hmac.new(creds["token_key"].encode(), digestmod=hashlib.sha256)
    digester.update(f"{method}{uri}".encode())

    # Step 2: HMAC over the first 13 chars of the formatted datetime
    datetime_formatted = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "+00:00"
    digester = hmac.new(digester.digest(), digestmod=hashlib.sha256)
    digester.update(datetime_formatted[:13].encode())

    # Step 3: HMAC over the request body (if any)
    digester = hmac.new(digester.digest(), digestmod=hashlib.sha256)

    body = None
    body_label = "<empty>"

    if body_file_name:
        with open(body_file_name, "rb") as f:
            file_bytes = f.read()
        digester.update(file_bytes)
        body = file_bytes
        body_label = f"{body_file_name} ({len(body)} bytes)"
    elif body_json is not None:
        body = json.dumps(body_json).encode()
        digester.update(body)
        body_label = f"<json: {len(body)} bytes>"

    signature = base64.b64encode(digester.digest()).decode()
    url = f"{creds['bh_url']}{uri}"

    if body_file_name and body_file_name.endswith(".zip"):
        content_type = "application/zip-compressed"
    else:
        content_type = "application/json"

    headers = {
        "User-Agent": "simple-uploader-v0.1",
        "Authorization": f"bhesignature {creds['token_id']}",
        "RequestDate": datetime_formatted,
        "Signature": signature,
        "Content-Type": content_type,
    }

    vlog(f"→ {method} {url}")
    vlog(f"  Headers: { {k: v for k, v in headers.items() if k != 'Authorization'} }")
    vlog(f"  Auth:    {headers['Authorization'][:30]}...")
    vlog(f"  Body:    {body_label}")

    resp = requests.request(method, url, headers=headers, data=body)

    vlog(f"← HTTP {resp.status_code}")
    vlog(f"  Response headers: {dict(resp.headers)}")
    vlog(f"  Response body:    {resp.text[:2000]}")

    if resp.status_code not in (200, 201, 202, 204):
        raise RuntimeError(f"Unexpected HTTP status code: {resp.status_code} — {resp.text}")

    if not resp.content:
        return {}

    return resp.json()


def upload_data(data_file_name: str, creds: dict) -> None:
    """Start an upload job, POST the file, then end the job."""
    upload_job = query_bloodhound_api("/api/v2/file-upload/start", "POST", creds)
    job_id = upload_job["data"]["id"]
    log.info("Processing job ID: %s", job_id)

    query_bloodhound_api(f"/api/v2/file-upload/{job_id}", "POST", creds, body_file_name=data_file_name)
    query_bloodhound_api(f"/api/v2/file-upload/{job_id}/end", "POST", creds)

    log.info("Data uploaded successfully for job ID: %s", job_id)


def clear_database(creds: dict) -> None:
    """Clear all collected graph data, ingest history, and quality history."""
    payload = {
        "deleteCollectedGraphData": True,
        "deleteFileIngestHistory": True,
        "deleteDataQualityHistory": True,
        "deleteAssetGroupSelectors": [0],
    }
    log.info("Clearing database...")
    query_bloodhound_api("/api/v2/clear-database", "POST", creds, body_json=payload)
    log.info("Database cleared successfully.")


def process_file(path: str, creds: dict) -> None:
    upload_data(path, creds)


def collect_files_from_dir(directory: Path) -> list:
    """Recursively find all .json and .zip files in a directory."""
    if not directory.exists():
        print(f"[!] Directory '{directory}' does not exist.")
        return []
    if not directory.is_dir():
        print(f"[!] '{directory}' is not a directory. Use -z/--zip to specify a zip file.")
        return []
    files = [p for p in directory.rglob("*") if p.is_file() and p.suffix in (".json", ".zip")]
    if not files:
        print(f"[!] No .json or .zip files found in '{directory}'.")
    return files


def collect_zip(zip_path: Path) -> list:
    """Validate and return a single zip file."""
    if not zip_path.exists():
        print(f"[!] Zip file '{zip_path}' does not exist.")
        return []
    if not zip_path.is_file():
        print(f"[!] '{zip_path}' is not a file.")
        return []
    if zip_path.suffix != ".zip":
        print(f"[!] '{zip_path}' is not a .zip file.")
        return []
    return [zip_path]


def main():
    global VERBOSE

    parser = argparse.ArgumentParser(description="BloodHound CE Uploader")
    parser.add_argument("-u", "--url",      default="http://localhost:8080", help="BloodHound URL")
    parser.add_argument("-i", "--tokenid",  required=True, help="BloodHound Token ID")
    parser.add_argument("-k", "--tokenkey", required=True, help="BloodHound Token Key")
    parser.add_argument("-d", "--dir",      help="Directory to scan for .json/.zip files")
    parser.add_argument("-z", "--zip",      help="Single .zip file to upload", dest="zipfile")
    parser.add_argument("-c", "--clear",    action="store_true", help="Clear all data from the database")
    parser.add_argument("-v", "--verbose",  action="store_true", help="Enable verbose debug output")
    args = parser.parse_args()

    VERBOSE = args.verbose
    banner()

    creds = {
        "bh_url":    args.url,
        "token_id":  args.tokenid,
        "token_key": args.tokenkey,
    }

    vlog(f"URL:       {creds['bh_url']}")
    vlog(f"Token ID:  {creds['token_id']}")
    vlog(f"Token Key: {creds['token_key'][:6]}...")

    if not args.clear and not args.dir and not args.zipfile:
        parser.error("You must specify at least one of: -d/--dir, -z/--zip, -c/--clear")

    if args.clear and (args.dir or args.zipfile):
        parser.error("-c/--clear cannot be combined with -d/--dir or -z/--zip")

    if args.dir and args.zipfile:
        parser.error("Specify only one of -d/--dir or -z/--zip, not both")

    # --clear runs first; can be combined with an upload in one command
    if args.clear:
        try:
            clear_database(creds)
        except Exception as e:
            print(f"[!] Error clearing database: {e}")
            sys.exit(1)

    if args.dir or args.zipfile:
        if args.zipfile:
            files = collect_zip(Path(args.zipfile))
        else:
            files = collect_files_from_dir(Path(args.dir))

        if not files:
            sys.exit(1)

        log.info("Found %d file(s) to upload.", len(files))

        for path in files:
            size_mb = path.stat().st_size / 1024 / 1024
            log.info("Uploading file %s, size: %.2f MB", path, size_mb)
            if size_mb > 20_000:
                log.warning(
                    "File %s is quite large, will most likely fail. "
                    "Use chophound to make it smaller or compress it using zip. Skipping.",
                    path,
                )
            else:
                try:
                    process_file(str(path), creds)
                except Exception as e:
                    print(f"[!] Error processing file {path}: {e}")


if __name__ == "__main__":
    main()
