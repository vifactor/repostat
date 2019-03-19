# gitstats
Forked gitstats: git history statistics analizer

The idea is to modernize the existing tool:
 - refactor by using Jinja templates
 - replace self-made calls to git with calls to either PythonGit or pygit2 libraries
 - embed good-looking (bokeh?, gnuplot html?) graphs instead of gnuplot ones
 - add author contribution plots
___
## gitstats Usage
**Sample:**
`python3 gitstats -coutput=[csv,html] -cproject_name=ProjectNameSample [git-repo-folder] [output-folder]`

### Args
#### output
**valid values**: csv, html  
**csv**: export basics repo statistic to csv files:  
    - activity_month_of_year.csv : monthly statistic
    - commits.csv : all commit info. Merge commit ignored
    - authors.csv : statistic about authors
    - general.csv : main statistic info about rep  
CSV export useful for import into any RDBMS and made any custom statistics.  
All CSV export files has "Project Name" and "Repo Name" columns. After csv imported any RDBMS can use this field for higher dimension of analysis.

**html**: this value is the default. Generate and show the statistics in html format. This is useful for human usage.
#### project_name
This param is only used in csv export.  
Repo's project name. A complex project has frontend repo, backend repo, DB repo...etc.  
When export the repo statistic you can group the details with this field.   
