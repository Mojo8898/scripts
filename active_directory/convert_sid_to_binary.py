#!/usr/bin/python3

import argparse
import struct

def convert_string_sid_to_binary(string_sid):
    # Split the SID into parts
    parts = string_sid.split("-")
    if parts[0] != "S":
        raise ValueError("Invalid SID format.")

    # Parse the SID components
    revision = int(parts[1])
    identifier_authority = int(parts[2])
    sub_authorities = list(map(int, parts[3:]))

    # Build the binary SID
    binary_sid = struct.pack("B", revision)  # Revision
    binary_sid += struct.pack("B", len(sub_authorities))  # Number of sub-authorities
    binary_sid += struct.pack(">Q", identifier_authority)[2:]  # Identifier authority (6 bytes)
    for sub_auth in sub_authorities:
        binary_sid += struct.pack("<I", sub_auth)  # Sub-authorities (4 bytes each)

    # Convert to hexadecimal representation
    binary_sid_hex = binary_sid.hex()
    return f"0x{binary_sid_hex}"

def main():
    parser = argparse.ArgumentParser(description="Convert a string SID to its binary representation in hexadecimal format.")
    parser.add_argument("sid", type=str, help="The string SID to convert.")
    args = parser.parse_args()

    try:
        binary_sid_hex = convert_string_sid_to_binary(args.sid)
        print(binary_sid_hex)
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
