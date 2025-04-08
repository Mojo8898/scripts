#!/usr/bin/python3

import base64
import struct
import argparse

def decode_sid(base64_sid):
    try:
        raw_sid = base64.b64decode(base64_sid)
        sid = "S-" + str(raw_sid[0])  # SID revision level
        sub_auth_count = raw_sid[1]  # Sub-authority count
        identifier_authority = int.from_bytes(raw_sid[2:8], 'big')
        sid += "-" + str(identifier_authority)
        for i in range(sub_auth_count):
            sub_authority = struct.unpack("<I", raw_sid[8 + i*4:12 + i*4])[0]
            sid += "-" + str(sub_authority)
        return sid
    except Exception as e:
        return f"Error decoding SID: {e}"

def main():
    parser = argparse.ArgumentParser(description="Decode a Raw Base64-encoded SIDHistory Attribute.")
    parser.add_argument("base64_sid", help="Base64-encoded SID to decode")
    args = parser.parse_args()
    decoded_sid = decode_sid(args.base64_sid)
    print(decoded_sid)

if __name__ == "__main__":
    main()
