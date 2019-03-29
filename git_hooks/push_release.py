#!/usr/bin/env python3
import sys
import subprocess
import re

# TODO: do not perform any actions if not on 'master' branch
# get most recent tag name in current branch
git_tag_string = subprocess.check_output(['git', 'describe', '--abbrev=0', '--tags']).decode().strip()

# check if this is a version tag of type: vN.N[.N], e.g. "v0.1"

if re.fullmatch(r'^v\d+\.\d+(\.\d+)?\Z', git_tag_string):
    print('the most recent version tag is:', git_tag_string)

# NOTE: for debug purposes (without push) use exit code different from 0
sys.exit(0)
