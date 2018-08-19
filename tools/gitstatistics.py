import pygit2 as git
import datetime


class GitStatistics:
    def __init__(self, path):
        """
        :param path: path to a repository
        """
        self.repo = git.Repository(path)
        self.authors = self.fetch_authors()
        self.tags = self.fetch_tags_info()

    def fetch_authors(self):
        """
        e.g.
        {'Stefano Mosconi': {'lines_removed': 1, 'last_commit_stamp': 1302027851, 'active_days': set(['2011-04-05']),
                             'lines_added': 1, 'commits': 1, 'first_commit_stamp': 1302027851,
                             'last_active_day': '2011-04-05'}
        """
        result = {}
        for child_commit in self.repo.walk(self.repo.head.target, git.GIT_SORT_TIME):
            is_merge_commit = False
            if len(child_commit.parents) == 0:
                # initial commit
                st = child_commit.tree.diff_to_tree(swap=True).stats
            elif len(child_commit.parents) == 1:
                parent_commit = child_commit.parents[0]
                st = self.repo.diff(parent_commit, child_commit).stats
            else:  # if len(child_commit.parents) == 2 (merge commit)
                is_merge_commit = True
            commit_day_str = datetime.datetime.fromtimestamp(child_commit.author.time).strftime('%Y-%m-%d')
            author_name = child_commit.author.name.encode('utf-8')
            if author_name not in result:
                result[author_name] = {
                    'lines_removed': st.deletions if not is_merge_commit else 0,
                    'lines_added': st.insertions if not is_merge_commit else 0,
                    'active_days': {commit_day_str},
                    'commits': 1,
                    'first_commit_stamp': child_commit.author.time,
                    'last_commit_stamp': child_commit.author.time,
                }
            else:
                result[author_name]['lines_removed'] += st.deletions if not is_merge_commit else 0
                result[author_name]['lines_added'] += st.insertions if not is_merge_commit else 0
                result[author_name]['active_days'].add(commit_day_str)
                result[author_name]['commits'] += 1
                if result[author_name]['first_commit_stamp'] > child_commit.author.time:
                    result[author_name]['first_commit_stamp'] = child_commit.author.time
                if result[author_name]['last_commit_stamp'] < child_commit.author.time:
                    result[author_name]['last_commit_stamp'] = child_commit.author.time

        # it seems that there is a mistake (or my misunderstanding) in 'last_active_day' value
        # my calculations give are not the same as those done by Heikki Hokkanen for this parameter
        for author in result:
            last_active_day = datetime.datetime.fromtimestamp(result[author]['last_commit_stamp']).strftime('%Y-%m-%d')
            result[author]['last_active_day'] = last_active_day

        return result

    def fetch_tags_info(self):
        tags = filter(lambda refobj: refobj.name.startswith('refs/tags'), self.repo.listall_reference_objects())
        commit_tag = {refobj.peel().oid: refobj.shorthand for refobj in tags}

        result = {refobj.shorthand: {
            'stamp': refobj.peel().author.time,
            'date': datetime.datetime.fromtimestamp(refobj.peel().author.time).strftime('%Y-%m-%d'),
            'hash': str(refobj.target)} for refobj in tags}

        authors = {}
        commit_count = 0
        for commit in self.repo.walk(self.repo.head.target, git.GIT_SORT_TOPOLOGICAL | git.GIT_SORT_REVERSE):
            commit_count += 1
            authors[commit.author.name] = authors.get(commit.author.name, 0) + 1
            if commit.oid in commit_tag.keys():
                tagname = commit_tag[commit.oid]
                result[tagname]['commits'] = commit_count
                result[tagname]['authors'] = authors

                commit_count = 0
                authors = {}

        return result
