import pygit2 as git
from datetime import datetime
import warnings
import os
from distutils import version

from tools.timeit import Timeit


class GitStatistics:
    is_mailmap_supported = True if version.LooseVersion(git.LIBGIT2_VERSION) >= '0.28.0' else False

    def __init__(self, path, fetch_contribution=False, fetch_tags=True):
        """
        :param path: path to a repository
        """
        self.repo = git.Repository(path)
        if GitStatistics.is_mailmap_supported:
            self.mailmap = git.Mailmap.from_repository(self.repo)

            def mapsig(sig: git.Signature):
                try:
                    mapped_signature = self.mailmap.resolve_signature(sig)
                except ValueError as e:
                    name = sig.name
                    email = sig.email
                    if not name:
                        name = "Empty Empty"
                        warnings.warn(f"{str(e)}. Name will be replaced with '{name}'")
                    if not email:
                        email = "empty@empty.empty"
                        warnings.warn(f"{str(e)}. Email will be replaced with '{email}'")
                    return git.Signature(name, email, sig.time, sig.offset, 'utf-8')
                else:
                    return mapped_signature

            self.signature_mapper = mapsig
        else:
            self.signature_mapper = lambda signature: signature

        self.created_time_stamp = datetime.now().timestamp()
        self.repo_name = os.path.basename(os.path.abspath(path))
        self.analysed_branch = self.repo.head.shorthand

        if fetch_contribution:
            # this is slow
            self.contribution = self.fetch_contributors()
        else:
            self.contribution = {}
        if fetch_tags:
            self.tags = self.fetch_tags_info()
        else:
            self.tags = {}

        self.changes_history, self.total_lines_added, self.total_lines_removed, self.total_lines_count \
            = self.fetch_total_history()

        # timestamp -> files count
        self.files_by_stamp = self._get_files_count_by_timestamp()

        # extension -> files, lines, size
        self.extensions = self.get_current_files_info()
        self.total_files_count = sum(v['files'] for k, v in self.extensions.items())
        self.total_tree_size = sum(v['size'] for k, v in self.extensions.items())

    def _get_files_count_by_timestamp(self):
        files_by_stamp = {}
        for commit in self.repo.walk(self.repo.head.target, git.GIT_SORT_TIME):
            diff = commit.tree.diff_to_tree()
            files_count = len(diff)
            # committer timestamp is chosen as we want to know when number of files changed on current branch
            # author.time gives time stamp of the commit creation
            timestamp = commit.committer.time
            files_by_stamp[timestamp] = files_count
        return files_by_stamp

    @staticmethod
    def _get_file_extension(git_file_path, max_ext_length=5):
        filename = os.path.basename(git_file_path)
        basename_parts = filename.split('.')
        ext = basename_parts[1] if len(basename_parts) == 2 and basename_parts[0] else ''
        if len(ext) > max_ext_length:
            ext = ''
        return ext

    def get_current_files_info(self):
        """
        :return: returns total files count and distribution of lines and files count by file extensions
        """
        head_commit = self.repo.revparse_single('HEAD')
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

    @classmethod
    def get_fetching_tool_info(cls):
        # could be bare git-subprocess invokation, PythonGit package, etc.
        return '{} v.{}'.format(git.__name__, git.LIBGIT2_VERSION)

    @Timeit("Fetching tags info")
    def fetch_tags_info(self):
        tags = [refobj for refobj in self.repo.listall_reference_objects() if refobj.name.startswith('refs/tags')]
        commit_tag = {refobj.peel().oid: refobj.shorthand for refobj in tags}

        result = {refobj.shorthand: {
            'stamp': refobj.peel().author.time,
            'date': datetime.fromtimestamp(refobj.peel().author.time).strftime('%Y-%m-%d'),
            'hash': str(refobj.target)} for refobj in tags}

        authors = {}
        commit_count = 0
        for commit in self.repo.walk(self.repo.head.target, git.GIT_SORT_TOPOLOGICAL | git.GIT_SORT_REVERSE):
            commit_count += 1
            commit_author = self.signature_mapper(commit.author)
            authors[commit_author.name] = authors.get(commit_author.name, 0) + 1
            if commit.oid in commit_tag.keys():
                tagname = commit_tag[commit.oid]
                result[tagname]['commits'] = commit_count
                result[tagname]['authors'] = authors

                commit_count = 0
                authors = {}

        return result

    @Timeit("Fetching current tree contributors")
    def fetch_contributors(self):
        head_commit = self.repo.head.peel()
        contribution = {}

        submodules_paths = self.repo.listall_submodules()
        diff_to_tree = head_commit.tree.diff_to_tree()
        diff_len = len(list(diff_to_tree))
        i = 0
        for p in diff_to_tree:
            file_to_blame = p.delta.new_file.path
            if file_to_blame not in submodules_paths and not p.delta.is_binary:
                blob_blame = self.repo.blame(file_to_blame)
                for blame_hunk in blob_blame:
                    hunk_committer = blame_hunk.final_committer
                    if not hunk_committer:
                        # if committer configured an empty email when created commit
                        # blame hunk corresponding to that commit will produce a None signature
                        # the following substitutes hunk's final committer with an author of the commit
                        hunk_committer = self.repo[blame_hunk.orig_commit_id].author
                    committer = self.signature_mapper(hunk_committer)
                    contribution[committer.name] = contribution.get(committer.name, 0) + blame_hunk.lines_in_hunk
            i += 1
            print(f"Working... ({i} / {diff_len})", end="\r", flush=True)

        return contribution

    def build_history_item(self, child_commit, stat) -> dict:
        author = self.signature_mapper(child_commit.author)
        return {
            'files': stat.files_changed,
            'ins': stat.insertions,
            'del': stat.deletions,
            'author': author.name,
            'author_mail': author.email,
            'is_merge': len(child_commit.parents) > 1,
            'commit_time': child_commit.commit_time,
            'oid': child_commit.oid,
            'parent_ids': child_commit.parent_ids
        }

    @Timeit("Fetching total history")
    def fetch_total_history(self):
        history = {}
        child_commit = self.repo.head.peel()
        timestamps = []
        while len(child_commit.parents) != 0:
            # taking [0]-parent is equivalent of '--first-parent -m' options
            parent_commit = child_commit.parents[0]
            st = self.repo.diff(parent_commit, child_commit).stats
            history[child_commit.author.time] = self.build_history_item(child_commit, st)
            timestamps.append(child_commit.author.time)
            child_commit = parent_commit
        # initial commit does not have parent, so we take diff to empty tree
        st = child_commit.tree.diff_to_tree(swap=True).stats
        history[child_commit.author.time] = self.build_history_item(child_commit, st)

        timestamps.append(child_commit.author.time)

        lines_count = 0
        lines_added = 0
        lines_removed = 0
        timestamps.reverse()
        for t in timestamps:
            lines_added += history[t]['ins']
            lines_removed += history[t]['del']
            lines_count += history[t]['ins'] - history[t]['del']
            history[t]['lines'] = lines_count
        return history, lines_added, lines_removed, lines_count

    def get_stamp_created(self):
        return self.created_time_stamp
