#!/usr/bin/env python3

import argparse
import os
import stat
import subprocess
import sys
from shutil import copyfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--force', action='store_true', default=False)
    args = parser.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    hook_file_src_path = os.path.join(
        here, 'git_hooks', 'push_release.py'
    )

    git_dir = subprocess.check_output(['git', 'rev-parse', '--git-dir'])
    hook_file_install_path = os.path.join(
        os.path.abspath(git_dir.decode().strip()), 'hooks', 'pre-push'
    )

    if not args.force and os.path.exists(hook_file_install_path):
            sys.stderr.write('error: pre-push hook already exists at %s\n\n' % hook_file_install_path)
            parser.print_help()
            sys.exit(2)

    copyfile(hook_file_src_path, hook_file_install_path)
    os.chmod(hook_file_install_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)


if __name__ == '__main__':
    main()
    sys.stdout.write('pre-push hook installed.\n')
