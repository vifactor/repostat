import time
import os
import zlib
import pickle
import datetime
from .gitstatistics import GitStatistics


class DataCollector:
    """Manages data collection from a revision control repository."""

    conf: dict = None

    def __init__(self, config):
        self.stamp_created = time.time()
        self.cache = {}
        self.conf = config

        # name -> {commits, first_commit_stamp, last_commit_stamp, last_active_day, active_days,
        #  lines_added,
        #  lines_removed}
        self.authors = {}

        self.total_commits = 0
        self.total_files = 0
        self.authors_by_commits = 0

        self.files_by_stamp = {}  # stamp -> files

        # extensions
        self.extensions = {}  # extension -> files, lines

    ##
    # This should be the main function to extract data from the repository.
    def collect(self, project_directory):
        self.dir = project_directory
        if not self.conf['project_name']:
            self.projectname = os.path.basename(os.path.abspath(project_directory))
        else:
            self.projectname = self.conf['project_name']

    ##
    # Load cacheable data
    def loadCache(self, cachefile):
        if not os.path.exists(cachefile):
            return
        print('Loading cache...')
        f = open(cachefile, 'rb')
        try:
            self.cache = pickle.loads(zlib.decompress(f.read()))
        except:
            # temporary hack to upgrade non-compressed caches
            f.seek(0)
            self.cache = pickle.load(f)
        f.close()

    ##
    # Save cacheable data
    def saveCache(self, cachefile):
        print('Saving cache...')
        tempfile = cachefile + '.tmp'
        f = open(tempfile, 'wb')
        # pickle.dump(self.cache, f)
        data = zlib.compress(pickle.dumps(self.cache))
        f.write(data)
        f.close()
        try:
            os.remove(cachefile)
        except OSError:
            pass
        os.rename(tempfile, cachefile)


class GitDataCollector(DataCollector):

    # dict['author'] = { 'commits': 512 } - ...key(dict, 'commits')
    @staticmethod
    def getkeyssortedbyvaluekey(d, key):
        return [el[1] for el in sorted([(d[el][key], el) for el in d.keys()])]

    def collect(self, project_directory):
        DataCollector.collect(self, project_directory)
        self.repo_statistics = GitStatistics(project_directory)

        self.analysed_branch = self.repo_statistics.repo.head.shorthand
        self.authors = self.repo_statistics.authors
        self.changes_by_date_by_author = self.repo_statistics.author_changes_history

        if 'files_in_tree' not in self.cache:
            self.cache['files_in_tree'] = {}
        revs_cached = []
        revs_to_read = []
        # look up rev in cache and take info from cache if found
        # if not append rev to list of rev to read from repo
        for ts, tree_id in self.repo_statistics.get_revisions():
            # if cache empty then add time and rev to list of new rev's
            # otherwise try to read needed info from cache
            if tree_id in self.cache['files_in_tree'].keys():
                revs_cached.append((ts, self.cache['files_in_tree'][tree_id]))
            else:
                revs_to_read.append((ts, tree_id))

        # update cache with new revisions and append then to general list
        for ts, rev in revs_to_read:
            diff = self.repo_statistics.get_files_info(rev)
            count = len(diff)
            self.cache['files_in_tree'][rev] = count
            revs_cached.append((ts, count))

        for (stamp, files) in revs_cached:
            self.files_by_stamp[stamp] = files
        self.total_commits = len(self.files_by_stamp)

        ext_dat = {}
        for p in self.repo_statistics.get_files_info('HEAD'):
            filename = os.path.basename(p.delta.old_file.path)
            basename_ext = filename.split('.')
            ext = basename_ext[1] if len(basename_ext) == 2 and basename_ext[0] else ''
            if len(ext) > self.conf['max_ext_length']:
                ext = ''
            if ext not in ext_dat:
                ext_dat[ext] = {'files': 0, 'lines': 0}
            # unclear what first two entries of the tuple mean, for each file they were equal to 0
            _, _, lines_count = p.line_stats
            ext_dat[ext]['lines'] += lines_count
            ext_dat[ext]['files'] += 1
        self.extensions = ext_dat
        self.total_files = sum(v['files'] for k, v in ext_dat.items())

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

    def getAuthorInfo(self, author):
        return self.authors[author]

    def getAuthors(self, limit=None):
        res = GitDataCollector.getkeyssortedbyvaluekey(self.authors, 'commits')
        res.reverse()
        return res[:limit]

    def getTotalCommits(self):
        return self.total_commits

    def getTotalFiles(self):
        return self.total_files
