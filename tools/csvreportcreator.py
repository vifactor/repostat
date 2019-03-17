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

class GeneralDictionaryExport():
	
	@staticmethod
	def export(fileName: str, data: dict, exportKeyAsField: bool = True, keyFieldName: str = 'key'):
		with open(fileName, 'w', newline='') as csvfile:
			fieldnames = list(data[list(data.keys())[0]].keys())
			if exportKeyAsField:
				fieldnames.append(keyFieldName)

			writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';', quotechar='"')
			
			writer.writeheader()
			for key, line in data.items():
				print_line = line
				if exportKeyAsField:
					print_line = dict(line)
					print_line[keyFieldName] = key
				writer.writerow(print_line)
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
		#export authors
		AuthorCsvExporter.exportAuthors(os.path.join(path, "authors.csv"), data.authors, aditionalInfo)
		#export commits
		CommitCsvExporter.exportCommits(os.path.join(path, "commits.csv"), data.commits, aditionalInfo)

		###
		# Activity
		
		#month of year
		linesAddedMonthly = data.get_lines_insertions_by_month()
		linesRemovedMonthly = data.get_lines_deletions_by_month()
		monthStatistic = {}
		for mm in data.author_year_monthly:
			monthStatistic[mm]={
				'Project Name': self.projectname,
				'Repo name': data.reponame,
				'Month': mm,
				'Lines added': linesAddedMonthly.get(mm, 0),
				'Lines removed': linesRemovedMonthly.get(mm, 0),
				'Author count': len(data.author_year_monthly.get(mm, {})),
				'Commits': data.activity_year_monthly.get(mm, 0)
			}
		GeneralDictionaryExport.export(path + '/activity_month_of_year.csv', monthStatistic, False)

