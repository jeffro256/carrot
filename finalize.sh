#!/usr/bin/bash

cd -- "$( dirname -- "$0" )"
cd src
./dumb_md_enumerate.py carrot_raw.md | ./dumb_citations.py > ../carrot.md

