#!/usr/bin/env python3

import argparse

def process_sid(input_string):
    prefix = 'S-1-5-21-'

    # Split the input string after the constant prefix
    components = input_string.split(prefix, 1)
    if len(components) > 1:
        remaining_string = components[1]
        split_values = remaining_string.split('-')
        output_list = []
        for i in split_values:
            decimal_number = int(i)
            hexadecimal_value = hex(decimal_number)[2:].zfill(8)
            little = ' '.join([hexadecimal_value[i:i+2] for i in range(len(hexadecimal_value)-2, -2, -2)])
            bytes_list = little.split()
            formatted_bytes = ', '.join([f"0x{byte.upper()}" for byte in bytes_list]) 
            output_list.append(formatted_bytes)
        final_output = ', '.join(output_list)
        print("0x01, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x05, 0x15, 0x00, 0x00, 0x00, " + final_output)
    else:
        print("Invalid SID format. Ensure the input string starts with 'S-1-5-21-'.")

def main():
    parser = argparse.ArgumentParser(description="Process a SID and convert it to a hex representation.")
    parser.add_argument("sid", type=str, help="The SID to process (e.g., S-1-5-21-2327345182-1863223493-3435513819)")
    args = parser.parse_args()
    process_sid(args.sid)

if __name__ == "__main__":
    main()
