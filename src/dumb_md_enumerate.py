#!/usr/bin/python3

import fileinput
import sys

""" Only supports ATX-style headers """

def parse_header(s):
    dep = 0
    for c in s:
        if c != '#':
            break
        dep += 1
    return dep - 1, s[dep:].lstrip()

header_stack = []

for line in fileinput.input():
    hd, title = parse_header(line)
    if hd <= 0:
        print(line, end='')
        continue
    while hd >= len(header_stack):
        header_stack.append(0)
    header_stack[hd] += 1
    del header_stack[hd+1:]
    section_str = '.'.join(map(str, header_stack[1:])) + ('.' if len(header_stack) == 2 else '')
    print('{} {} {}'.format('#' * (hd + 1), section_str, title), end='')
