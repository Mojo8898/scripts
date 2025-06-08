#!/usr/bin/python3

import json, sys

# how wide to allow certain columns before truncating
TRUNCATE = {
    "Enrollment Rights": 40,
    "[!] Vulnerabilities": 30,
    "[*] Remarks": 50
}

# rights to exclude
EXCLUDE_RIGHTS = [
    "Enterprise Read-only Domain Controllers",
    "Domain Admins",
    "Domain Controllers",
    "Enterprise Admins",
    "Enterprise Domain Controllers",
]

def load_json(path):
    with open(path) as f:
        return json.load(f)

def fmt_list(lst):
    return ", ".join(lst) if isinstance(lst, list) else str(lst)

def fmt_keys(d):
    if not isinstance(d, dict) or not d:
        return ""
    return "; ".join(d.keys())

def truncate(s, max_len):
    return s if len(s) <= max_len else s[: max_len - 3] + "..."

def main(json_path):
    data = load_json(json_path)
    templates = data.get("Certificate Templates", {})

    headers = [
        "Template Name",
        "Client Authentication",
        "Any Purpose",
        "Enrollee Supplies Subject",
        "Enrollment Rights",
        "[!] Vulnerabilities",
        "[*] Remarks"
    ]

    # build & filter rows
    raw_rows = []
    for tpl in templates.values():
        orig = tpl.get("Permissions", {}) \
                 .get("Enrollment Permissions", {}) \
                 .get("Enrollment Rights", [])
        filtered = [r for r in orig if not any(exc in r for exc in EXCLUDE_RIGHTS)]
        if not filtered:
            continue

        raw_rows.append({
            "Template Name":                tpl.get("Template Name", ""),
            "Client Authentication":        str(tpl.get("Client Authentication", "")),
            "Any Purpose":                  str(tpl.get("Any Purpose", "")),
            "Enrollee Supplies Subject":    str(tpl.get("Enrollee Supplies Subject", "")),
            "Enrollment Rights":            fmt_list(filtered),
            "[!] Vulnerabilities":          fmt_keys(tpl.get("[!] Vulnerabilities", {})),
            "[*] Remarks":                  fmt_keys(tpl.get("[*] Remarks", {})),
        })

    # truncate long cells & compute widths
    widths = {h: len(h) for h in headers}
    rows = []
    for row in raw_rows:
        nr = {}
        for h in headers:
            val = row[h]
            # if h in TRUNCATE:
            #     val = truncate(val, TRUNCATE[h])
            nr[h] = val
            widths[h] = max(widths[h], len(val))
        rows.append(nr)

    # build format string
    fmt = "  ".join(f"{{:<{widths[h]}}}" for h in headers)

    # print table
    print(fmt.format(*headers))
    print("  ".join("-" * widths[h] for h in headers))
    for r in rows:
        print(fmt.format(*(r[h] for h in headers)))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <offsec_enabled_Certipy.json>")
        sys.exit(1)
    main(sys.argv[1])
