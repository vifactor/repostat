#!/usr/bin/env python3
import sys
import subprocess
import re
import os
import json
from datetime import datetime
import pygit2 as git

HERE = os.path.dirname(os.path.abspath(__file__))
REPOSTAT_REPO = os.path.join(HERE, '..', '..')
RELEASE_DATA_FILE = os.path.join(REPOSTAT_REPO, 'release_data.json')


def fetch_contributors():
    repostat_repo = git.Repository(REPOSTAT_REPO)
    head_commit = repostat_repo.head.peel()
    contribution = {}

    submodules_paths = repostat_repo.listall_submodules()
    for p in head_commit.tree.diff_to_tree():
        file_to_blame = p.delta.new_file.path
        if file_to_blame not in submodules_paths:
            blob_blame = repostat_repo.blame(file_to_blame)
            for blame_hunk in blob_blame:
                contribution[blame_hunk.final_committer.name] = contribution.get(blame_hunk.final_committer.name, 0) \
                                                                + blame_hunk.lines_in_hunk

    # this gives only the contributors to the current code tree, not all the commiters to the project
    contribution = sorted(contribution.items(), key=lambda kv: kv[1], reverse=True)
    return [contributor for contributor, lines_contributed in contribution]


# TODO: do not perform any actions if not on 'master' branch
# get most recent tag name in current branch
git_tag_string = subprocess.check_output(['git', 'describe', '--abbrev=0', '--tags']).decode().strip()

# check if this is a version tag of type: vN.N[.N], e.g. "v0.1"
if re.fullmatch(r'^v\d+\.\d+(\.\d+)?\Z', git_tag_string):
    print('the most recent version tag is:', git_tag_string)

try:
    release_json_file = open(RELEASE_DATA_FILE)
except FileNotFoundError as ex:
    release_data = {}
    print("{}: {}".format(ex.strerror, ex.filename))
else:
    release_data = json.load(release_json_file)
    print(release_data)
    release_json_file.close()

if not release_data or release_data['develop_version'] != git_tag_string:
    # create new release data and store, create commit
    release_data['develop_version'] = git_tag_string

    release_tag_timestamp = subprocess.check_output(['git', 'log', '-1', '--format=%at', git_tag_string]).decode().strip()
    release_tag_date_yymm = datetime.fromtimestamp(int(release_tag_timestamp)).strftime('%Y-%m')
    release_data['user_version'] = release_tag_date_yymm

    contributors = fetch_contributors()
    release_data['contributors'] = contributors

    with open(RELEASE_DATA_FILE, 'w') as release_json_file:
        print("Release data is being updated:", release_data)
        json.dump(release_data, release_json_file, indent=4)

    # create commit with release data
    subprocess.check_output(['git', 'add', '{}'.format(RELEASE_DATA_FILE)])
    subprocess.check_output(['git', 'commit', '-m "Release {}"'.format(git_tag_string)])
    # move the most recent tag onto this new commit
    # TODO: move tag with message
    subprocess.check_output(['git', 'tag', '-f', git_tag_string])

# NOTE: for debug purposes (without push) use exit code different from 0
sys.exit(0)
