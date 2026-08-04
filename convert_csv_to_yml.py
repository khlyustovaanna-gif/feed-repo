#!/usr/bin/env python3
# simple CSV -> YML converter for Yandex.Direct feed
# Usage: python3 convert_csv_to_yml.py feed_template.csv docs/feed.xml

import sys, csv, os
from xml.sax.saxutils import escape

def row_to_offer(r):
    return f'''  <offer id="{escape(r.get('id',''))}" available="true">
    <url>{escape(r.get('url',''))}</url>
    <price>{escape(r.get('price',''))}</price>
    <currencyId>{escape(r.get('currencyId','RUB'))}</currencyId>
    <categoryId>{escape(r.get('categoryId','0'))}</categoryId>
    <picture>{escape(r.get('picture',''))}</picture>
    <name>{escape(r.get('name',''))}</name>
    <description>{escape(r.get('description',''))}</description>
    <vendor>{escape(r.get('vendor',''))}</vendor>
    <model>{escape(r.get('model',''))}</model>
  </offer>'''

def convert(csv_path, out_path):
    rows = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<yml_catalog date="2020-01-01 00:00">\n  <shop>\n')
        f.write('    <name>Shop</name>\n    <company>Company</company>\n    <url>https://example.com/</url>\n    <currencies>\n      <currency id="RUB" rate="1"/>\n    </currencies>\n    <categories>\n      <category id="0">All</category>\n    </categories>\n    <offers>\n')
        for r in rows:
            f.write(row_to_offer(r) + "\n")
        f.write("    </offers>\n  </shop>\n</yml_catalog>\n")
    print("Wrote", out_path)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: convert_csv_to_yml.py input.csv output.xml")
        sys.exit(2)
    convert(sys.argv[1], sys.argv[2])
