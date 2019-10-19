import os
import datetime
import calendar
import itertools
import time
import collections
import glob
from jinja2 import Environment, FileSystemLoader
from analysis.gitstatistics import GitStatistics
from tools.shellhelper import get_pipe_output
from tools.configuration import Configuration
from tools import sort_keys_by_value_of_key

def getkeyssortedbyvalues(a_dict):
    return [el[1] for el in sorted([(el[1], el[0]) for el in a_dict.items()])]


class HTMLReportCreator(object):
    recent_activity_period_weeks = 32

    def __init__(self, config: Configuration, repo_stat):
        self.data = None
        self.path = None
        self.configuration = config
        self.assets_path = os.path.join(self.configuration.repostat_root_dir, "assets")

        self.git_repo_statistics = repo_stat

        templates_dir = os.path.join(self.configuration.repostat_root_dir, 'templates')
        self.j2_env = Environment(loader=FileSystemLoader(templates_dir), trim_blocks=True)
        self.j2_env.filters['to_month_name_abr'] = lambda im: calendar.month_abbr[im]
        self.j2_env.filters['to_weekday_name'] = lambda i: calendar.day_name[i]
        self.j2_env.filters['to_ratio'] = lambda val, max_val: (float(val) / max_val) if max_val != 0 else 0
        self.j2_env.filters['to_percentage'] = lambda val, max_val: (100 * float(val) / max_val) if max_val != 0 else 0
        self.j2_env.filters['to_intensity'] = lambda val, max_val: 127 + int((float(val) / max_val) * 128)

    def _save_recent_activity_data(self):
        # generate weeks to show (previous N weeks from now)
        now = datetime.datetime.now()
        weeks = []
        stampcur = now
        for i in range(0, self.recent_activity_period_weeks):
            weeks.insert(0, stampcur.strftime('%Y-%W'))
            stampcur -= datetime.timedelta(7)

        with open(os.path.join(self.path, 'recent_activity.dat'), 'w') as f:
            for i in range(0, self.recent_activity_period_weeks):
                commits = self.git_repo_statistics.recent_activity_by_week.get(weeks[i], 0)
                f.write("%d %d\n" % (self.recent_activity_period_weeks - i - 1, commits))

    def _get_authors(self, limit=None):
        res = sort_keys_by_value_of_key(self.git_repo_statistics.authors, 'commits')
        res.reverse()
        return res[:limit]

    def create(self, path):
        self.path = path

        ###
        # General
        general_html = self.render_general_page(None)
        with open(os.path.join(path, "general.html"), 'w', encoding='utf-8') as f:
            f.write(general_html)

        ###
        # Activity
        activity_html = self.render_activity_page(None)
        with open(os.path.join(path, "activity.html"), 'w', encoding='utf-8') as f:
            f.write(activity_html)

        # Commits by current year's months
        today_date = datetime.date.today()
        current_year = today_date.year
        with open(os.path.join(path, 'commits_by_year_month.dat'), 'w') as fg:
            for month in range(1, 13):
                yymm = datetime.date(current_year, month, 1).strftime("%Y-%m")
                fg.write('%s %s\n' % (yymm, self.git_repo_statistics.monthly_commits_timeline.get(yymm, 0)))

        # Commits by year
        with open(os.path.join(path, 'commits_by_year.dat'), 'w') as fg:
            for yy in sorted(self.git_repo_statistics.yearly_commits_timeline.keys()):
                fg.write('%d %d\n' % (yy, self.git_repo_statistics.yearly_commits_timeline[yy]))

        ###
        # Authors
        authors_html = self.render_authors_page(None)
        with open(os.path.join(path, "authors.html"), 'w', encoding='utf-8') as f:
            f.write(authors_html.decode('utf-8'))

        # cumulated added lines by
        # author. to save memory,
        # changes_by_date_by_author[stamp][author] is defined
        # only at points where author commits.
        # lines_by_authors allows us to generate all the
        # points in the .dat file.
        lines_by_authors = {}
        lines_by_other_authors = {}

        # Don't rely on getAuthors to give the same order each
        # time. Be robust and keep the list in a variable.
        commits_by_authors = {}
        commits_by_other_authors = {}

        authors_to_plot = self._get_authors(self.configuration['max_authors'])
        with open(os.path.join(path, 'lines_of_code_by_author.dat'), 'w') as fgl, \
                open(os.path.join(path, 'commits_by_author.dat'), 'w') as fgc:
            header_row = '"timestamp" ' + ' '.join('"{0}"'.format(w) for w in authors_to_plot) + ' ' \
                         + '"others"' + '\n'
            fgl.write(header_row)
            fgc.write(header_row)
            for stamp in sorted(self.git_repo_statistics.author_changes_history.keys()):
                fgl.write('%d' % stamp)
                fgc.write('%d' % stamp)
                for author in authors_to_plot:
                    if author in self.git_repo_statistics.author_changes_history[stamp].keys():
                        lines_by_authors[author] = self.git_repo_statistics.author_changes_history[stamp][author]['lines_added']
                        commits_by_authors[author] = self.git_repo_statistics.author_changes_history[stamp][author]['commits']
                    fgl.write(' %d' % lines_by_authors.get(author, 0))
                    fgc.write(' %d' % commits_by_authors.get(author, 0))

                if len(authors_to_plot) > self.configuration['max_authors']:
                    for author in self.git_repo_statistics.author_changes_history[stamp].keys():
                        if author not in authors_to_plot:
                            lines_by_other_authors[author] = self.git_repo_statistics.author_changes_history[stamp][author]['lines_added']
                            commits_by_other_authors[author] = self.git_repo_statistics.author_changes_history[stamp][author]['commits']
                    fgl.write(' %d' % sum(lines for lines in lines_by_other_authors.values()))
                    fgc.write(' %d' % sum(commits for commits in commits_by_other_authors.values()))
                fgl.write('\n')
                fgc.write('\n')

        # Domains
        domains_by_commits = sort_keys_by_value_of_key(self.git_repo_statistics.domains, 'commits')
        domains_by_commits.reverse()
        with open(os.path.join(path, 'domains.dat'), 'w') as fp:
            for i, domain in enumerate(domains_by_commits[:self.configuration['max_domains']]):
                info = self.git_repo_statistics.domains[domain]
                fp.write('%s %d %d\n' % (domain, i, info['commits']))

        ###
        # Files
        files_html = self.render_files_page(None)
        with open(os.path.join(path, "files.html"), 'w', encoding='utf-8') as f:
            f.write(files_html)

        with open(os.path.join(path, 'files_by_date.dat'), 'w') as fg:
            for timestamp in sorted(self.git_repo_statistics.files_by_stamp.keys()):
                fg.write('%d %d\n' % (timestamp, self.git_repo_statistics.files_by_stamp[timestamp]))

        with open(os.path.join(path, 'lines_of_code.dat'), 'w') as fg:
            for stamp in sorted(self.git_repo_statistics.changes_history.keys()):
                fg.write('%d %d\n' % (stamp, self.git_repo_statistics.changes_history[stamp]['lines']))

        ###
        # tags.html
        tags_html = self.render_tags_page(None)
        with open(os.path.join(path, "tags.html"), 'w', encoding='utf-8') as f:
            f.write(tags_html.decode('utf-8'))

        ###
        # about.html
        about_html = self.render_about_page()
        with open(os.path.join(path, "about.html"), 'w', encoding='utf-8') as f:
            f.write(about_html.decode('utf-8'))

        print('Generating graphs...')
        self.process_gnuplot_scripts(scripts_path=os.path.join(self.configuration.repostat_root_dir, 'gnuplot'),
                                     data_path=path,
                                     output_images_path=path)

    def render_general_page(self, data):
        date_format_str = '%Y-%m-%d %H:%M'
        first_commit_datetime = datetime.datetime.fromtimestamp(self.git_repo_statistics.first_commit_timestamp)
        last_commit_datetime = datetime.datetime.fromtimestamp(self.git_repo_statistics.last_commit_timestamp)
        # TODO: this conversion from old 'data' to new 'project data' should perhaps be removed in future
        project_data = {
            "name": self.git_repo_statistics.repo_name,
            "branch": self.git_repo_statistics.analysed_branch,
            "age": (last_commit_datetime - first_commit_datetime).days,
            "active_days_count": len(self.git_repo_statistics.active_days),
            "commits_count": self.git_repo_statistics.total_commits,
            "authors_count": len(self.git_repo_statistics.authors),
            "files_count": self.git_repo_statistics.total_files_count,
            "total_lines_count": self.git_repo_statistics.total_lines_count,
            "added_lines_count": self.git_repo_statistics.total_lines_added,
            "removed_lines_count": self.git_repo_statistics.total_lines_removed,
            "first_commit_date": first_commit_datetime.strftime(date_format_str),
            "last_commit_date": last_commit_datetime.strftime(date_format_str)
        }

        generation_data = {
            "datetime": datetime.datetime.today().strftime(date_format_str),
            "duration": "{0:.3f}".format(time.time() - self.git_repo_statistics.get_stamp_created())
        }

        # load and render template
        template_rendered = self.j2_env.get_template('general.html').render(
            project=project_data,
            generation=generation_data,
            page_title="General",
            assets_path=self.assets_path
        )
        return template_rendered

    def render_activity_page(self, data):
        # TODO: this conversion from old 'data' to new 'project data' should perhaps be removed in future
        project_data = {
            'hourly_activity': [],
            'weekday_hourly_activity': {},
            'weekday_activity': {},
            'timezones_activity': collections.OrderedDict(sorted(self.git_repo_statistics.timezones.items(), key=lambda n: int(n[0]))),
            'month_in_year_activity': self.git_repo_statistics.activity_monthly,
            'weekday_hour_max_commits_count': self.git_repo_statistics.max_weekly_hourly_activity
        }

        self._save_recent_activity_data()

        hour_of_day = self.git_repo_statistics.get_hourly_activity()
        for i in range(0, 24):
            if i in hour_of_day:
                project_data['hourly_activity'].append(hour_of_day[i])
            else:
                project_data['hourly_activity'].append(0)

        for weekday in range(len(calendar.day_name)):
            project_data['weekday_hourly_activity'][weekday] = []
            weekday_commits = 0
            for hour in range(0, 24):
                try:
                    commits = self.git_repo_statistics.activity_weekly_hourly[weekday][hour]
                    weekday_commits += commits
                except KeyError:
                    commits = 0
                if commits != 0:
                    project_data['weekday_hourly_activity'][weekday].append(commits)
                else:
                    project_data['weekday_hourly_activity'][weekday].append(commits)
            project_data['weekday_activity'][weekday] = weekday_commits

        # load and render template
        template_rendered = self.j2_env.get_template('activity.html').render(
            project=project_data,
            page_title="Activity",
            assets_path=self.assets_path
        )
        return template_rendered

    def render_authors_page(self, data):
        # TODO: this conversion from old 'data' to new 'project data' should perhaps be removed in future
        project_data = {
            'top_authors': [],
            'non_top_authors': [],
            'authors_top': self.configuration['authors_top'],
            'total_commits_count': self.git_repo_statistics.total_commits
        }

        all_authors = self._get_authors()
        if len(all_authors) > self.configuration['max_authors']:
            rest = all_authors[self.configuration['max_authors']:]
            project_data['non_top_authors'] = rest

        project_data['months'] = []
        # print out only recent conf['max_authors_of_months'] authors of the month
        iter_months_with_authors = reversed(sorted(self.git_repo_statistics.author_of_month.keys()))
        for yymm in itertools.islice(iter_months_with_authors, self.configuration['max_authors_of_months']):
            authordict = self.git_repo_statistics.author_of_month[yymm]
            authors = getkeyssortedbyvalues(authordict)
            authors.reverse()
            commits = self.git_repo_statistics.author_of_month[yymm][authors[0]]
            next = ', '.join(authors[1:self.configuration['authors_top'] + 1])

            month_dict = {
                'date': yymm,
                'top_author': {'name': authors[0], 'commits_count': commits},
                'next_top_authors': next,
                'all_commits_count': self.git_repo_statistics.monthly_commits_timeline[yymm]
            }

            project_data['months'].append(month_dict)

        project_data['years'] = []
        for yy in reversed(sorted(self.git_repo_statistics.author_of_year.keys())):
            authordict = self.git_repo_statistics.author_of_year[yy]
            authors = getkeyssortedbyvalues(authordict)
            authors.reverse()
            commits = self.git_repo_statistics.author_of_year[yy][authors[0]]
            next = ', '.join(authors[1:self.configuration['authors_top'] + 1])

            year_dict = {
                'date': yy,
                'top_author': {'name': authors[0], 'commits_count': commits},
                'next_top_authors': next,
                'all_commits_count': self.git_repo_statistics.yearly_commits_timeline[yy]
            }

            project_data['years'].append(year_dict)

        for author in all_authors[:self.configuration['max_authors']]:
            info = self.git_repo_statistics.authors[author]
            author_dict = {
                'name': author,
                'commits_count': info['commits'],
                'lines_added_count': info['lines_added'],
                'lines_removed_count': info['lines_removed'],
                'first_commit_date': info['date_first'],
                'latest_commit_date': info['date_last'],
                'contributed_days_count': info['timedelta'],
                'active_days_count': len(info['active_days']),
            }

            project_data['top_authors'].append(author_dict)

        # load and render template
        template_rendered = self.j2_env.get_template('authors.html').render(
            project=project_data,
            page_title="Authors",
            assets_path=self.assets_path
        )
        return template_rendered.encode('utf-8')

    def render_files_page(self, data):
        # TODO: this conversion from old 'data' to new 'project data' should perhaps be removed in future
        project_data = {
            'files_count': self.git_repo_statistics.total_files_count,
            'lines_count': self.git_repo_statistics.total_lines_count,
            'size': self.git_repo_statistics.total_tree_size,
            'files': []
        }

        for ext in sorted(self.git_repo_statistics.extensions.keys()):
            files = self.git_repo_statistics.extensions[ext]['files']
            lines = self.git_repo_statistics.extensions[ext]['lines']
            file_type_dict = {"extension": ext,
                              "count": files,
                              "lines_count": lines
                              }
            project_data['files'].append(file_type_dict)

        # load and render template
        template_rendered = self.j2_env.get_template('files.html').render(
            project=project_data,
            page_title="Files",
            assets_path=self.assets_path
        )
        return template_rendered

    def render_tags_page(self, data):
        # TODO: this conversion from old 'data' to new 'project data' should perhaps be removed in future
        project_data = {
            'tags_count': len(self.git_repo_statistics.tags),
            'tags': []
        }

        # TODO: fix error occurring when a tag name and project name are the same
        """
        fatal: ambiguous argument 'gitstats': both revision and filename
        Use '--' to separate paths from revisions, like this:
        'git <command> [<revision>...] -- [<file>...]'
        """

        # TODO: refactor the following code
        tags_sorted_by_date_desc = [el[1] for el in reversed(sorted([(el[1]['date'], el[0]) for el in self.git_repo_statistics.tags.items()]))]
        for tag in tags_sorted_by_date_desc:
            # there are tags containing no commits
            if 'authors' in self.git_repo_statistics.tags[tag].keys():
                authorinfo = []
                authors_by_commits = getkeyssortedbyvalues(self.git_repo_statistics.tags[tag]['authors'])
                for i in reversed(authors_by_commits):
                    authorinfo.append('%s (%d)' % (i, self.git_repo_statistics.tags[tag]['authors'][i]))
                tag_dict = {
                    'name': tag,
                    'date': self.git_repo_statistics.tags[tag]['date'],
                    'commits_count': self.git_repo_statistics.tags[tag]['commits'],
                    'authors': ', '.join(authorinfo)
                }
                project_data['tags'].append(tag_dict)

        # load and render template
        template_rendered = self.j2_env.get_template('tags.html').render(
            project=project_data,
            page_title="Tags",
            assets_path=self.assets_path
        )
        return template_rendered.encode('utf-8')

    def render_about_page(self):
        page_data = {
            "url": "https://github.com/vifactor/repostat",
            "version": self.configuration.get_release_data_info()['user_version'],
            "tools": [GitStatistics.get_fetching_tool_info(),
                      self.configuration.get_jinja_version(),
                      'gnuplot ' + self.configuration.get_gnuplot_version()],
            "contributors": [author for author in self.configuration.get_release_data_info()['contributors']]
        }

        template_rendered = self.j2_env.get_template('about.html').render(
            repostat=page_data,
            page_title="About",
            assets_path=self.assets_path
        )
        return template_rendered.encode('utf-8')

    def process_gnuplot_scripts(self,scripts_path, data_path, output_images_path):
        scripts = glob.glob(os.path.join(scripts_path, '*.plot'))
        os.chdir(output_images_path)
        for script in scripts:
            gnuplot_command = '%s -e "data_folder=\'%s\'" "%s"' % (self.configuration.gnuplot_executable, data_path, script)
            out = get_pipe_output([gnuplot_command])
            if len(out) > 0:
                print(out)
