import time
import os
import csv
import datetime
from .gitstatistics  import GitStatistics
from .gitstatistics  import CommitDictFactory
from .reportCreator import ReportCreator


class AuthorCsvExporter():

	@staticmethod
	def exportAuthors(fileName: str, authors: dict, aditionalValues: dict):
		with open(fileName, 'w', newline='') as csvfile:
			fieldnames = ['projectname', 'reponame', 'author_name', 'lines_added', 'lines_removed', 'commits', 'first_commit_stamp', 'last_commit_stamp',
				'last_active_day', 'timedelta', 'active_days', 'date_first', 'date_last', 'place_by_commits']
			#
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';', quotechar='"')
			
			writer.writeheader()
			for authorName, authorData in authors.items():
				tmp = dict(authorData)
				tmp.update(aditionalValues)
				writer.writerow(tmp)
			csvfile.close()

class CommitCsvExporter():

	@staticmethod
	def exportCommits(fileName: str, commits: dict, aditionalValues: dict):
		with open(fileName, 'w', newline='') as csvfile:
			fieldnames = CommitDictFactory.FIELD_LIST + ['reponame', 'projectname']

			writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';', quotechar='"')
			
			writer.writeheader()
			for commit in commits:
				tmp = dict(commit)
				tmp.update(aditionalValues)
				writer.writerow(tmp)
			csvfile.close()

class CSVReportCreator(ReportCreator):
	def printHeader(self, f):
		return
	def printNav(self, f):
		return
	
	
	def getAdditionalFields(self, data: GitStatistics):
		return {"projectname": self.projectname,
			"reponame": data.reponame}

	def create(self, data: GitStatistics, path: str, config: dict):
		
		ReportCreator.create(self, data, path, config)

		#General info
		f = open(path + "/general.csv", 'w')
		format = '%Y-%m-%d %H:%M:%S'
		first_commit = datetime.datetime.fromtimestamp(data.first_commit_timestamp).strftime(format)
		last_commit = datetime.datetime.fromtimestamp(data.last_commit_timestamp).strftime(format)
		f.write('Project name;Repo name;Generated;Generation duration in seconds;Report Period Start (First commit);Report Period (Last commit);Age (days);Age (active days);\
Total Files;Total Lines;Total Lines added;Total Lines removed;Total Commits;Authors\n')
		f.write('%s;%s;%s;%d;%s;%s;%d;%d;%s;%s;%s;%s;%s;%s\n' % (self.projectname, data.reponame, datetime.datetime.now().strftime(format), time.time() - data.getStampCreated(), 
			first_commit, last_commit, data.getCommitDeltaDays(), len(data.getActiveDays()),
			data.getTotalFiles(), data.getTotalLineCount(), data.total_lines_added, data.total_lines_removed, data.getTotalCommits(), data.getTotalAuthors())) 
		f.close()
		aditionalInfo= self.getAdditionalFields(data)
		AuthorCsvExporter.exportAuthors(os.path.join(path, "authors.csv"), data.authors, aditionalInfo)
		CommitCsvExporter.exportCommits(os.path.join(path, "commits.csv"), data.commits, aditionalInfo)

		###
		# Activity
		return
		#month of year
		f = open(path + '/activity_month_of_year.csv', 'w')
		f.write('Project Name;Repo name;Month;Commit count;Commit percentage\n')
		for mm in range(1, 13):
			commits = 0
			if mm in data.activity_by_month_of_year:
				commits = data.activity_by_month_of_year[mm]
			f.write('%s;%s;%d;%d;%.2f\n' % (self.projectname, data.reponame, mm, commits, (100.0 * commits) / data.getTotalCommits()))
		f.close()

		# Commits by year/month
		#export to CSV
		f = open(path + "/activity_commit_year_month.csv", 'w')
		f.write('Project name;Repo name;Month;Commits;Lines added;Lines removed\n')
		for yymm in reversed(sorted(data.commits_by_month.keys())):
			f.write('%s;%s;%s;%d;%d;%d\n' % (self.projectname, data.reponame, yymm, data.commits_by_month.get(yymm,0), data.lines_added_by_month.get(yymm,0), 
				data.lines_removed_by_month.get(yymm,0)))
		f.close()



		# Commits by year
		f = open(path + "/activity_commit_year.csv", 'w')
		f.write('Project name;Repo name;Year;Commits; Commits percentage;Lines added;Lines removed\n')
		for yy in reversed(sorted(data.commits_by_year.keys())):
			f.write('%s;%s;%s;%d;%.2f;%d;%d\n' % (self.projectname, data.reponame, yy, data.commits_by_year.get(yy,0), (100.0 * data.commits_by_year.get(yy,0)) / data.getTotalCommits(), data.lines_added_by_year.get(yy,0), data.lines_removed_by_year.get(yy,0)))
		f.close()

		
		###
		# Authors
		f = open(path + '/authors.html', 'w')
		# Authors :: List of authors
		f.write('Project name;Repo name;Author;Commits; Commits percentage (%);+ lines;- lines;First commit;Last commit;Age;Active days;# by commits\n')
		for author in data.getAuthors():
			info = data.getAuthorInfo(author)
			f.write('%s;%s;%s;%d;%.2f;%d;%d;%s;%s;%s;%d;%d\n' % (self.projectname, data.reponame, author, info['commits'], info['commits_frac'], info['lines_added'], info['lines_removed'], info['date_first'], info['date_last'], info['timedelta'], len(info['active_days']), info['place_by_commits']))
		f.close()

		f = open(path + '/authors_lines_commits.csv', 'w')

		lines_by_authors = {} # cumulated added lines by
		# author. to save memory,
		# changes_by_date_by_author[stamp][author] is defined
		# only at points where author commits.
		# lines_by_authors allows us to generate all the
		# points in the .dat file.

		# Don't rely on getAuthors to give the same order each
		# time. Be robust and keep the list in a variable.
		commits_by_authors = {} # cumulated added lines by

		self.authors_to_plot = data.getAuthors()
		for author in self.authors_to_plot:
			lines_by_authors[author] = 0
			commits_by_authors[author] = 0
		f.write('Project name;Repo name;Author;Date,Lines added; Commits\n')
		for stamp in sorted(data.changes_by_date_by_author.keys()):
			for author in self.authors_to_plot:
				if author in data.changes_by_date_by_author[stamp].keys():
					lines_by_authors[author] = data.changes_by_date_by_author[stamp][author]['lines_added']
					commits_by_authors[author] = data.changes_by_date_by_author[stamp][author]['commits']
				f.write('%s;%s;%s;%s;%d;%d\n' % (self.projectname, data.reponame, author, datetime.datetime.fromtimestamp(float(stamp)), lines_by_authors[author], commits_by_authors[author]))
		f.close()

