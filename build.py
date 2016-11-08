#!/usr/bin/env python
import subprocess

# NB this is a hack and is dependent on position of paper number in the paper.
with open('paper.md') as i:
    paper_number = i.readlines()[4].strip() 

subprocess.check_call('pandoc paper.md -o {}.pdf'.format(paper_number).split())
