import os
import datetime
import calendar
import itertools
import time
import collections
import glob
from jinja2 import Environment, FileSystemLoader
from distutils.dir_util import copy_tree

from analysis.gitstatistics import GitStatistics
from analysis.gitrepository import GitRepository
from tools.shellhelper import get_pipe_output
from tools.configuration import Configuration
from tools import sort_keys_by_value_of_key

HERE = os.path.dirname(os.path.abspath(__file__))


class HTMLReportCreator(object):
    recent_activity_period_weeks = 32
    assets_subdir = "assets"
    templates_subdir = "templates"

    def __init__(self, config: Configuration, repo_stat: GitStatistics, repository: GitRepository):
        self.path = None
        self.configuration = config
        self.assets_path = os.path.join(HERE, self.assets_subdir)
        self.git_repo_statistics = repo_stat
        self.git_repository_statistics = repository
        self.has_tags_page = config.do_process_tags()

        self.common_rendering_data = {
            "assets_path": self.assets_path,
            "has_tags_page": self.has_tags_page
        }

        templates_dir = os.path.join(HERE, self.templates_subdir)
        self.j2_env = Environment(loader=FileSystemLoader(templates_dir), trim_blocks=True)
        self.j2_env.filters['to_month_name_abr'] = lambda im: calendar.month_abbr[im]
        self.j2_env.filters['to_weekday_name'] = lambda i: calendar.day_name[i]
        self.j2_env.filters['to_ratio'] = lambda val, max_val: (float(val) / max_val) if max_val != 0 else 0
        self.j2_env.filters['to_percentage'] = lambda val, max_val: (100 * float(val) / max_val) if max_val != 0 else 0
        self.j2_env.filters['to_intensity'] = lambda val, max_val: 127 + int((float(val) / max_val) * 128)

    def _save_recent_activity_data(self):
        recent_weekly_commits = self.git_repository_statistics.\
            get_recent_weekly_activity(self.recent_activity_period_weeks)
        with open(os.path.join(self.path, 'recent_activity.dat'), 'w') as f:
            for i, commits in enumerate(recent_weekly_commits):
                f.write("%d %d\n" % (self.recent_activity_period_weeks - i - 1, commits))

    def _get_authors(self, limit=None):
        res = sort_keys_by_value_of_key(self.git_repo_statistics.authors, 'commits', reverse=True)
        return res[:limit]

    def _bundle_assets(self):
        # copy assets to report output folder
        assets_local_abs_path = os.path.join(self.path, self.assets_subdir)
        copy_tree(src=self.assets_path, dst=assets_local_abs_path)
        # relative path to assets to embed into html pages
        self.assets_path = os.path.relpath(assets_local_abs_path, self.path)

    def create(self, path):
        self.path = path

        if self.configuration.is_report_relocatable():
            self._bundle_assets()
            self.common_rendering_data.update({
                "assets_path": self.assets_path
            })

        ###
        # General
        general_html = self.render_general_page()
        with open(os.path.join(path, "general.html"), 'w', encoding='utf-8') as f:
            f.write(general_html)

        try:
            # make the landing page for a web server
            os.symlink("general.html", os.path.join(path, "index.html"))
        except FileExistsError:
            # if symlink exists, it points to "general.html" so no need to re-create it
            # other solution would be to use approach from
            # https://stackoverflow.com/questions/8299386/modifying-a-symlink-in-python/8299671
            pass

        ###
        # Activity
        activity_html = self.render_activity_page()
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
        authors_html = self.render_authors_page()
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
                        lines_by_authors[author] = self.git_repo_statistics.author_changes_history[stamp][author][
                            'lines_added']
                        commits_by_authors[author] = self.git_repo_statistics.author_changes_history[stamp][author][
                            'commits']
                    fgl.write(' %d' % lines_by_authors.get(author, 0))
                    fgc.write(' %d' % commits_by_authors.get(author, 0))

                if len(authors_to_plot) > self.configuration['max_authors']:
                    for author in self.git_repo_statistics.author_changes_history[stamp].keys():
                        if author not in authors_to_plot:
                            lines_by_other_authors[author] = \
                                self.git_repo_statistics.author_changes_history[stamp][author]['lines_added']
                            commits_by_other_authors[author] = \
                                self.git_repo_statistics.author_changes_history[stamp][author]['commits']
                    fgl.write(' %d' % sum(lines for lines in lines_by_other_authors.values()))
                    fgc.write(' %d' % sum(commits for commits in commits_by_other_authors.values()))
                fgl.write('\n')
                fgc.write('\n')

        # Domains
        domains_by_commits = sort_keys_by_value_of_key(self.git_repo_statistics.domains, 'commits', reverse=True)
        with open(os.path.join(path, 'domains.dat'), 'w') as fp:
            for i, domain in enumerate(domains_by_commits[:self.configuration['max_domains']]):
                info = self.git_repo_statistics.domains[domain]
                fp.write('%s %d %d\n' % (domain, i, info['commits']))

        ###
        # Files
        files_html = self.render_files_page()
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

        if self.has_tags_page:
            tags_html = self.render_tags_page()
            with open(os.path.join(path, "tags.html"), 'w', encoding='utf-8') as f:
                f.write(tags_html.decode('utf-8'))

        ###
        # about.html
        about_html = self.render_about_page()
        with open(os.path.join(path, "about.html"), 'w', encoding='utf-8') as f:
            f.write(about_html.decode('utf-8'))

        print('Generating graphs...')
        self.process_gnuplot_scripts(scripts_path=os.path.join(HERE, 'gnuplot'),
                                     data_path=path,
                                     output_images_path=path)

    def render_general_page(self):
        date_format_str = '%Y-%m-%d %H:%M'
        first_commit_datetime = datetime.datetime.fromtimestamp(self.git_repository_statistics.first_commit_timestamp)
        last_commit_datetime = datetime.datetime.fromtimestamp(self.git_repository_statistics.last_commit_timestamp)
        # TODO: this conversion from old 'data' to new 'project data' should perhaps be removed in future
        project_data = {
            "name": self.git_repo_statistics.repo_name,
            "branch": self.git_repo_statistics.analysed_branch,
            "age": (last_commit_datetime - first_commit_datetime).days,
            "active_days_count": self.git_repository_statistics.active_days_count,
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
            **self.common_rendering_data
        )
        return template_rendered

    def render_activity_page(self):
        # TODO: this conversion from old 'data' to new 'project data' should perhaps be removed in future
        project_data = {
            'hourly_activity': [],
            'weekday_hourly_activity': {},
            'weekday_activity': {},
            'timezones_activity': collections.OrderedDict(
                sorted(self.git_repository_statistics.timezones_distribution.items(), key=lambda n: int(n[0]))),
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
            **self.common_rendering_data
        )
        return template_rendered

    def render_authors_page(self):
        # TODO: this conversion from old 'data' to new 'project data' should perhaps be removed in future
        project_data = {
            'top_authors': [],
            'non_top_authors': [],
            'authors_top': self.configuration['authors_top'],
            'total_commits_count': self.git_repo_statistics.total_commits,
            'total_lines_count': self.git_repo_statistics.total_lines_count
        }

        all_authors = self._get_authors()
        if len(all_authors) > self.configuration['max_authors']:
            project_data['non_top_authors'] = all_authors[self.configuration['max_authors']:]

        project_data['months'] = []
        # print out only recent conf['max_authors_of_months'] authors of the month
        iter_months_with_authors = sorted(self.git_repo_statistics.author_of_month.keys(), reverse=True)
        for yymm in itertools.islice(iter_months_with_authors, self.configuration['max_authors_of_months']):
            authors_dict = self.git_repo_statistics.author_of_month[yymm]
            authors = [name for name, _ in sorted(authors_dict.items(), key=lambda kv: kv[1], reverse=True)]
            commits = self.git_repo_statistics.author_of_month[yymm][authors[0]]
            next_top_authors_str = ', '.join(authors[1:self.configuration['authors_top'] + 1])

            month_dict = {
                'date': yymm,
                'top_author': {'name': authors[0], 'commits_count': commits},
                'next_top_authors': next_top_authors_str,
                'all_commits_count': self.git_repo_statistics.monthly_commits_timeline[yymm],
                'total_authors_count': len(self.git_repo_statistics.author_of_month[yymm])
            }

            project_data['months'].append(month_dict)

        project_data['years'] = []
        raw_authors_data = self.git_repository_statistics.get_authors_ranking_by_year()
        max_top_authors_index = self.configuration['authors_top'] + 1
        ordered_years = raw_authors_data.index.get_level_values(0).unique().sort_values(ascending=False)
        for y in ordered_years:
            authors_in_year = raw_authors_data.loc[y]
            project_data['years'].append({
                'date': y,
                'top_author': {'name': authors_in_year.index[0], 'commits_count': authors_in_year[0]},
                'next_top_authors': ', '.join(list(authors_in_year.index[1:max_top_authors_index])),
                'all_commits_count': authors_in_year.sum(),
                'total_authors_count': authors_in_year.size
            })

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
                'contribution': self.git_repo_statistics.contribution.get(author,
                                                                          0) if self.git_repo_statistics.contribution else None,
            }

            project_data['top_authors'].append(author_dict)

        # load and render template
        template_rendered = self.j2_env.get_template('authors.html').render(
            project=project_data,
            page_title="Authors",
            **self.common_rendering_data
        )
        return template_rendered.encode('utf-8')

    def render_files_page(self):
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
            **self.common_rendering_data
        )
        return template_rendered

    def render_tags_page(self):
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
        tags_sorted_by_date_desc = sort_keys_by_value_of_key(self.git_repo_statistics.tags, 'date', reverse=True)
        for tag in tags_sorted_by_date_desc:
            if 'max_recent_tags' in self.configuration \
                    and self.configuration['max_recent_tags'] <= len(project_data['tags']):
                break
            # there are tags containing no commits
            if 'authors' in self.git_repo_statistics.tags[tag].keys():
                authordict = self.git_repo_statistics.tags[tag]['authors']
                authors_by_commits = [
                    name for name, _ in sorted(authordict.items(), key=lambda kv: kv[1], reverse=True)
                ]
                authorinfo = []
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
            **self.common_rendering_data
        )
        return template_rendered.encode('utf-8')

    def render_about_page(self):
        repostat_version = self.configuration.get_release_data_info()['develop_version']
        repostat_version_date = self.configuration.get_release_data_info()['user_version']
        page_data = {
            "version": f"{repostat_version} ({repostat_version_date})",
            "tools": [GitStatistics.get_fetching_tool_info(),
                      self.configuration.get_jinja_version(),
                      'gnuplot ' + self.configuration.get_gnuplot_version()],
            "contributors": [author for author in self.configuration.get_release_data_info()['contributors']]
        }

        template_rendered = self.j2_env.get_template('about.html').render(
            repostat=page_data,
            page_title="About",
            **self.common_rendering_data
        )
        return template_rendered.encode('utf-8')

    def process_gnuplot_scripts(self, scripts_path, data_path, output_images_path):
        scripts = glob.glob(os.path.join(scripts_path, '*.plot'))
        os.chdir(output_images_path)
        for script in scripts:
            gnuplot_command = '%s -e "data_folder=\'%s\'" "%s"' % (
                self.configuration.gnuplot_executable, data_path, script)
            out = get_pipe_output([gnuplot_command])
            if len(out) > 0:
                print(out)
