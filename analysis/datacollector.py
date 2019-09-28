import time
import os
import datetime
import pygit2 as git
from .gitstatistics import GitStatistics


class GitDataCollector(object):

    def __init__(self, config: dict, project_directory):
        self.stamp_created = time.time()
        self.conf = config
        if not self.conf['project_name']:
            self.projectname = os.path.basename(os.path.abspath(project_directory))
        else:
            self.projectname = self.conf['project_name']

        self.repo_statistics = GitStatistics(project_directory)
        self.analysed_branch = self.repo_statistics.repo.head.shorthand

        # name -> {commits, first_commit_stamp, last_commit_stamp, last_active_day, active_days,
        #  lines_added,
        #  lines_removed}
        self.authors = self.repo_statistics.authors
        self.changes_by_date_by_author = self.repo_statistics.author_changes_history

        self.authors_by_commits = 0

        # timestamp -> files count
        self.files_by_stamp = self._get_files_count_by_timestamp()
        self.total_commits = len(self.files_by_stamp)

        # extension -> files, lines, size
        self.extensions = self.get_current_files_info()
        self.total_files = sum(v['files'] for k, v in self.extensions.items())

    # dict['author'] = { 'commits': 512 } - ...key(dict, 'commits')
    @staticmethod
    def getkeyssortedbyvaluekey(d, key):
        return [el[1] for el in sorted([(d[el][key], el) for el in d.keys()])]

    def _get_files_count_by_timestamp(self):
        files_by_stamp = {}
        for commit in self.repo_statistics.repo.walk(self.repo_statistics.repo.head.target, git.GIT_SORT_TIME):
            diff = commit.tree.diff_to_tree()
            files_count = len(diff)
            # committer timestamp is chosen as we want to know when number of files changed on current branch
            # author.time gives time stamp of the commit creation
            timestamp = commit.committer.time
            files_by_stamp[timestamp] = files_count
        return files_by_stamp

    def _get_file_extension(self, git_file_path):
        filename = os.path.basename(git_file_path)
        basename_parts = filename.split('.')
        ext = basename_parts[1] if len(basename_parts) == 2 and basename_parts[0] else ''
        if len(ext) > self.conf['max_ext_length']:
            ext = ''
        return ext

    def get_current_files_info(self):
        """
        :return: returns total files count and distribution of lines and files count by file extensions
        """
        head_commit = self.repo_statistics.repo.revparse_single('HEAD')
        head_commit_tree = head_commit.tree.diff_to_tree(swap=True)
        extensions = {}
        for p in head_commit_tree:
            ext = self._get_file_extension(p.delta.new_file.path)
            if ext not in extensions:
                extensions[ext] = {'files': 0, 'lines': 0, 'size': 0}
            _, lines_count, _ = p.line_stats
            extensions[ext]['lines'] += lines_count
            extensions[ext]['files'] += 1
            extensions[ext]['size'] += p.delta.new_file.size
        return extensions

    def refine(self):
        # authors
        # name -> {place_by_commits, date_first, date_last, timedelta}
        self.authors_by_commits = GitDataCollector.getkeyssortedbyvaluekey(self.authors, 'commits')
        self.authors_by_commits.reverse()  # most first
        for i, name in enumerate(self.authors_by_commits):
            self.authors[name]['place_by_commits'] = i + 1

        for name in self.authors.keys():
            a = self.authors[name]
            date_first = datetime.datetime.fromtimestamp(a['first_commit_stamp'])
            date_last = datetime.datetime.fromtimestamp(a['last_commit_stamp'])
            delta = (date_last - date_first).days
            a['date_first'] = date_first.strftime('%Y-%m-%d')
            a['date_last'] = date_last.strftime('%Y-%m-%d')
            a['timedelta'] = delta
            if 'lines_added' not in a: a['lines_added'] = 0
            if 'lines_removed' not in a: a['lines_removed'] = 0

    def get_author_info(self, author):
        return self.authors[author]

    def get_authors(self, limit=None):
        res = GitDataCollector.getkeyssortedbyvaluekey(self.authors, 'commits')
        res.reverse()
        return res[:limit]

    def get_total_commits(self):
        return self.total_commits

    def get_total_files(self):
        return self.total_files
