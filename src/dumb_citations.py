#!/usr/bin/python3

import fileinput
import re
import sys

"""
Converts `[citation](...)` markdown links into numbered `[X](...)` citation links and generates a
reference table replacing the string "*INSERT REFERENCES HERE*".
"""

def parse_citation_links(s, cit_no):
    CIT_LINK_PATTERN = r"\[citation\]\((.+?)\)"
    links = []
    m = re.search(CIT_LINK_PATTERN, s)
    while m:
        links.append(m.group(1))
        repl = f"[{cit_no}](\\1)"
        s = re.sub(CIT_LINK_PATTERN, repl, s, count=1)
        cit_no += 1
        m = re.search(CIT_LINK_PATTERN, s)
    return s, links

def make_reference_table(links):
    return '\n'.join('1. ' + link for link in links)

doc_links = []
cit_no = 1
for line in fileinput.input():
    processed_line, line_links = parse_citation_links(line, cit_no)
    doc_links.extend(line_links)
    cit_no += len(line_links)
    if '*INSERT REFERENCES HERE*' in processed_line:
        ref_table = make_reference_table(doc_links)
        processed_line = processed_line.replace('*INSERT REFERENCES HERE*', ref_table)
    print(processed_line, end='')
