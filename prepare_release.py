#!/usr/bin/env python2
"""
This script is supposed to be run before each release to update information like:
 - release version
 - contributed authors
 etc.
"""
import pygit2 as git
import os
from tools import generate_version_from


if __name__ == '__main__':
    repostat_repo = git.Repository(os.getcwd())
    head_commit = repostat_repo.head.peel()
    # TODO: check that current branch is 'master' (or checkout to 'master'?)
    # TODO: readout the version before opening file for writing and write only if version changed
    with open('VERSION', 'w') as f:
        version = generate_version_from(head_commit)
        f.write(version)
