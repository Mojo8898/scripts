#!/usr/bin/env python3

import argparse
import base64
import hashlib
import hmac
import json
import logging
import subprocess
import sys
import time
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

USER_QUERY = "/ui/explore?exploreSearchTab=cypher&cypherSearch=TUFUQ0ggcD1zaG9ydGVzdFBhdGgoKHQ6QmFzZSApLVs6T3duc3xHZW5lcmljQWxsfEdlbmVyaWNXcml0ZXxXcml0ZU93bmVyfFdyaXRlRGFjbHxNZW1iZXJPZnxGb3JjZUNoYW5nZVBhc3N3b3JkfEFsbEV4dGVuZGVkUmlnaHRzfEFkZE1lbWJlcnxIYXNTZXNzaW9ufEdQTGlua3xBbGxvd2VkVG9EZWxlZ2F0ZXxDb2VyY2VUb1RHVHxBbGxvd2VkVG9BY3R8QWRtaW5Ub3xDYW5QU1JlbW90ZXxDYW5SRFB8RXhlY3V0ZURDT018SGFzU0lESGlzdG9yeXxBZGRTZWxmfERDU3luY3xSZWFkTEFQU1Bhc3N3b3JkfFJlYWRHTVNBUGFzc3dvcmR8RHVtcFNNU0FQYXNzd29yZHxTUUxBZG1pbnxBZGRBbGxvd2VkVG9BY3R8V3JpdGVTUE58QWRkS2V5Q3JlZGVudGlhbExpbmt8U3luY0xBUFNQYXNzd29yZHxXcml0ZUFjY291bnRSZXN0cmljdGlvbnN8V3JpdGVHUExpbmt8R29sZGVuQ2VydHxBRENTRVNDMXxBRENTRVNDM3xBRENTRVNDNHxBRENTRVNDNmF8QURDU0VTQzZifEFEQ1NFU0M5YXxBRENTRVNDOWJ8QURDU0VTQzEwYXxBRENTRVNDMTBifEFEQ1NFU0MxM3xTeW5jZWRUb0VudHJhVXNlcnxDb2VyY2VBbmRSZWxheU5UTE1Ub1NNQnxDb2VyY2VBbmRSZWxheU5UTE1Ub0FEQ1N8V3JpdGVPd25lckxpbWl0ZWRSaWdodHN8T3duc0xpbWl0ZWRSaWdodHN8Q2xhaW1TcGVjaWFsSWRlbnRpdHl8Q29lcmNlQW5kUmVsYXlOVExNVG9MREFQfENvZXJjZUFuZFJlbGF5TlRMTVRvTERBUFN8Q29udGFpbnNJZGVudGl0eXxQcm9wYWdhdGVzQUNFc1RvfEdQT0FwcGxpZXNUb3xDYW5BcHBseUdQT3xIYXNUcnVzdEtleXN8TWFuYWdlQ0F8TWFuYWdlQ2VydGlmaWNhdGVzfENvbnRhaW5zfERDRm9yfFNhbWVGb3Jlc3RUcnVzdHxTcG9vZlNJREhpc3Rvcnl8QWJ1c2VUR1REZWxlZ2F0aW9uKjEuLl0tPihzOkdyb3VwKSkKV0hFUkUgcy5kaXN0aW5ndWlzaGVkbmFtZSBTVEFSVFMgV0lUSCAnQ049UkVNT1RFIE1BTkFHRU1FTlQgVVNFUlMsJyBBTkQgKHQ6VXNlciBvciB0OkNvbXB1dGVyKSBBTkQgTk9ORShuIElOIG5vZGVzKHApIFdIRVJFIG46VGFnX1RpZXJfWmVybykgQU5EIHM8PnQKUkVUVVJOIHAKTElNSVQgMTAwMA%3D%3D&searchType=cypher"
DA_QUERY = "/ui/explore?exploreSearchTab=cypher&cypherSearch=TUFUQ0ggcD1zaG9ydGVzdFBhdGgoKHQ6R3JvdXApPC1bOk93bnN8R2VuZXJpY0FsbHxHZW5lcmljV3JpdGV8V3JpdGVPd25lcnxXcml0ZURhY2x8TWVtYmVyT2Z8Rm9yY2VDaGFuZ2VQYXNzd29yZHxBbGxFeHRlbmRlZFJpZ2h0c3xBZGRNZW1iZXJ8SGFzU2Vzc2lvbnxHUExpbmt8QWxsb3dlZFRvRGVsZWdhdGV8Q29lcmNlVG9UR1R8QWxsb3dlZFRvQWN0fEFkbWluVG98Q2FuUFNSZW1vdGV8Q2FuUkRQfEV4ZWN1dGVEQ09NfEhhc1NJREhpc3Rvcnl8QWRkU2VsZnxEQ1N5bmN8UmVhZExBUFNQYXNzd29yZHxSZWFkR01TQVBhc3N3b3JkfER1bXBTTVNBUGFzc3dvcmR8U1FMQWRtaW58QWRkQWxsb3dlZFRvQWN0fFdyaXRlU1BOfEFkZEtleUNyZWRlbnRpYWxMaW5rfFN5bmNMQVBTUGFzc3dvcmR8V3JpdGVBY2NvdW50UmVzdHJpY3Rpb25zfFdyaXRlR1BMaW5rfEdvbGRlbkNlcnR8QURDU0VTQzF8QURDU0VTQzN8QURDU0VTQzR8QURDU0VTQzZhfEFEQ1NFU0M2YnxBRENTRVNDOWF8QURDU0VTQzlifEFEQ1NFU0MxMGF8QURDU0VTQzEwYnxBRENTRVNDMTN8U3luY2VkVG9FbnRyYVVzZXJ8Q29lcmNlQW5kUmVsYXlOVExNVG9TTUJ8Q29lcmNlQW5kUmVsYXlOVExNVG9BRENTfFdyaXRlT3duZXJMaW1pdGVkUmlnaHRzfE93bnNMaW1pdGVkUmlnaHRzfENsYWltU3BlY2lhbElkZW50aXR5fENvZXJjZUFuZFJlbGF5TlRMTVRvTERBUHxDb2VyY2VBbmRSZWxheU5UTE1Ub0xEQVBTfENvbnRhaW5zSWRlbnRpdHl8UHJvcGFnYXRlc0FDRXNUb3xHUE9BcHBsaWVzVG98Q2FuQXBwbHlHUE98SGFzVHJ1c3RLZXlzfE1hbmFnZUNBfE1hbmFnZUNlcnRpZmljYXRlc3xDb250YWluc3xEQ0ZvcnxTYW1lRm9yZXN0VHJ1c3R8U3Bvb2ZTSURIaXN0b3J5fEFidXNlVEdURGVsZWdhdGlvbioxLi5dLShzOkJhc2UpKQpXSEVSRSB0Lm9iamVjdGlkIEVORFMgV0lUSCAnLTUxMicgQU5EIHM8PnQKUkVUVVJOIHAKTElNSVQgMTAwMA%3D%3D&searchType=cypher"

STATUS_LABELS = {
    1: "Running",
    2: "Complete",
    3: "Failed",
    4: "Cancelled",
    5: "TimedOut",
    6: "Ingesting",
}

TERMINAL_STATUSES = {2, 3, 4, 5}

READY_SENTINEL = "Cache successfully reset by datapipe daemon"
DOCKER_CONTAINER = "bloodhound-bloodhound-1"


def banner():
    print(BANNER)


def vlog(*args, **kwargs):
    if VERBOSE:
        print("[VERBOSE]", *args, **kwargs)


# ── API helpers ────────────────────────────────────────────────────────────────

def has_upload_jobs(creds: dict) -> bool:
    """Return True if any upload jobs exist."""
    jobs = query_bloodhound_api("/api/v2/file-upload", "GET", creds)
    return bool(jobs.get("data"))


def query_bloodhound_api(uri: str, method: str, creds: dict,
                         body_file_name: str = "", body_json: dict = None) -> dict:
    digester = hmac.new(creds["token_key"].encode(), digestmod=hashlib.sha256)
    digester.update(f"{method}{uri}".encode())

    datetime_formatted = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "+00:00"
    digester = hmac.new(digester.digest(), digestmod=hashlib.sha256)
    digester.update(datetime_formatted[:13].encode())

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

    content_type = "application/zip-compressed" if (body_file_name and body_file_name.endswith(".zip")) else "application/json"

    headers = {
        "User-Agent":    "simple-uploader-v0.1",
        "Authorization": f"bhesignature {creds['token_id']}",
        "RequestDate":   datetime_formatted,
        "Signature":     signature,
        "Content-Type":  content_type,
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

    return {} if not resp.content else resp.json()


# ── Upload ─────────────────────────────────────────────────────────────────────

def upload_data(data_file_name: str, creds: dict) -> int:
    """Start an upload job, POST the file, end the job. Returns the job ID."""
    upload_job = query_bloodhound_api("/api/v2/file-upload/start", "POST", creds)
    job_id = upload_job["data"]["id"]
    log.info("Processing job ID: %s", job_id)

    query_bloodhound_api(f"/api/v2/file-upload/{job_id}", "POST", creds, body_file_name=data_file_name)
    query_bloodhound_api(f"/api/v2/file-upload/{job_id}/end", "POST", creds)

    log.info("Data uploaded successfully for job ID: %s", job_id)
    return job_id


def clear_database(creds: dict) -> None:
    payload = {
        "deleteCollectedGraphData":  True,
        "deleteFileIngestHistory":   True,
        "deleteDataQualityHistory":  True,
        "deleteAssetGroupSelectors": [0],
    }
    log.info("Clearing database...")
    query_bloodhound_api("/api/v2/clear-database", "POST", creds, body_json=payload)
    log.info("Database cleared successfully.")


def process_file(path: str, creds: dict) -> int:
    return upload_data(path, creds)


def collect_files_from_dir(directory: Path) -> list:
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


# ── Readiness wait ─────────────────────────────────────────────────────────────

def wait_for_ready(since: datetime, timeout: float = 60.0) -> None:
    """Tail docker logs since the clear was issued, block until BloodHound signals ready."""
    log.info("Waiting for BloodHound to finish post-clear analysis (watching docker logs)...")

    # Format as RFC3339 for docker --since flag
    since_str = since.strftime("%Y-%m-%dT%H:%M:%SZ")

    proc = subprocess.Popen(
        ["docker", "logs", DOCKER_CONTAINER, "--follow", "--since", since_str],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    deadline = time.time() + timeout
    try:
        for line in proc.stdout:
            vlog(f"[docker] {line.rstrip()}")
            if READY_SENTINEL in line:
                log.info("BloodHound is ready — '%s' seen in logs.", READY_SENTINEL)
                return
            if time.time() > deadline:
                raise RuntimeError(
                    f"BloodHound did not become ready within {timeout}s — sentinel line never appeared."
                )
    finally:
        proc.kill()
        proc.wait()


# ── Polling ────────────────────────────────────────────────────────────────────

def get_upload_jobs(creds: dict) -> list:
    return query_bloodhound_api("/api/v2/file-upload", "GET", creds).get("data", [])


def open_firefox(bh_url: str) -> None:
    for query in (USER_QUERY, DA_QUERY):
        subprocess.Popen(
            ["firefox", bh_url.rstrip("/") + query],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )


def poll_job(creds: dict, job_id: int, interval: float) -> None:
    log.info("Polling job %d...", job_id)
    last_status = None

    while True:
        try:
            jobs = get_upload_jobs(creds)
        except Exception as e:
            log.error("Failed to fetch jobs: %s", e)
            time.sleep(interval)
            continue

        matches = [j for j in jobs if j.get("id") == job_id]
        if not matches:
            log.warning("Job ID %d not found yet, retrying...", job_id)
            time.sleep(interval)
            continue

        job        = matches[0]
        status     = job.get("status")
        status_msg = job.get("status_message") or STATUS_LABELS.get(status, f"Unknown ({status})")

        if status != last_status:
            total   = job.get("total_files", 0)
            failed  = job.get("failed_files", 0)
            partial = job.get("partial_failed_files", 0)
            log.info("Job %d | Status: %s (%d) | Files: %d total, %d failed, %d partial",
                     job_id, status_msg, status, total, failed, partial)
            last_status = status

        if status == 2:
            log.info("Job %d completed successfully. Launching Firefox...", job_id)
            open_firefox(creds["bh_url"])
            return
        elif status in TERMINAL_STATUSES:
            log.error("Job %d ended with status: %s (%d). Exiting.", job_id, status_msg, status)
            sys.exit(1)

        time.sleep(interval)


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    global VERBOSE

    parser = argparse.ArgumentParser(description="BloodHound CE Uploader")
    parser.add_argument("-u", "--url",      default="http://localhost:8080", help="BloodHound URL")
    parser.add_argument("-i", "--tokenid",  required=True,  help="BloodHound Token ID")
    parser.add_argument("-k", "--tokenkey", required=True,  help="BloodHound Token Key")
    parser.add_argument("-d", "--dir",      help="Directory to scan for .json/.zip files")
    parser.add_argument("-z", "--zip",      help="Single .zip file to upload", dest="zipfile")
    parser.add_argument("-c", "--clear",    action="store_true", help="Clear all data from the database")
    parser.add_argument("-p", "--poll",     action="store_true", help="Poll upload job status and open Firefox on completion")
    parser.add_argument("-n", "--interval", type=float, default=0.5, help="Poll interval in seconds (default: 0.5)")
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

    if args.dir and args.zipfile:
        parser.error("Specify only one of -d/--dir or -z/--zip, not both")

    if args.poll and not (args.dir or args.zipfile):
        parser.error("-p/--poll requires an upload target (-d/--dir or -z/--zip)")

    upload_requested = bool(args.dir or args.zipfile)

    if args.clear:
        if not has_upload_jobs(creds):
            log.info("No existing upload jobs found — skipping clear and readiness wait.")
        else:
            try:
                clear_time = datetime.now(timezone.utc)
                clear_database(creds)
            except Exception as e:
                print(f"[!] Error clearing database: {e}")
                sys.exit(1)

            if upload_requested:
                try:
                    wait_for_ready(since=clear_time)
                except Exception as e:
                    print(f"[!] {e}")
                    sys.exit(1)

    if upload_requested:
        files = collect_zip(Path(args.zipfile)) if args.zipfile else collect_files_from_dir(Path(args.dir))

        if not files:
            sys.exit(1)

        log.info("Found %d file(s) to upload.", len(files))

        last_job_id = None
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
                    last_job_id = process_file(str(path), creds)
                except Exception as e:
                    print(f"[!] Error processing file {path}: {e}")

        if args.poll and last_job_id is not None:
            poll_job(creds, last_job_id, args.interval)


if __name__ == "__main__":
    main()
