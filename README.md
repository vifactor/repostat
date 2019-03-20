# gitstats
Forked gitstats: git history statistics analizer

The idea is to modernize the existing tool:
 - refactor by using Jinja templates
 - replace self-made calls to git with calls to either PythonGit or pygit2 libraries
 - embed good-looking (bokeh?, gnuplot html?) graphs instead of gnuplot ones
 - add author contribution plots
 
 Requirements:
 - python 3
 - gnuplot
 - jinja2
 - pygit2
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
All CSV export files has "Project Name" and "Repo Name" columns.  
After csv imported any RDBMS can use this field for higher dimension of analysis.

**html**: this value is the default. Generate and show the statistics in html format. This is useful for human usage.
#### project_name
This param is only used in csv export.  
Repo's project name. A complex project has frontend repo, backend repo, DB repo...etc.  
When export the repo statistic you can group the details with this field.   

## export_repos Usage
export_repos.py is a tool script to export well structured git repos.  
Requiered folder structure:  

* root  
  * project1  
    * GitRepo  
    * GitRepo1  
    * GitRepon  
  * project2  
    * p2repo1  
    * p2repo2  

`python export_repos.py [root-folder] [output-folder]`

### Args
#### root-folder
root folder location. This folder contain the project folders, and the project folder contain the project repositories.

#### output-folder
The script create same folder structure in the output folder as root-folder.  
The repos folders will contain the csv export files.

* root  
  * project1  
    * GitRepo  
      * general.csv
      * authors.csv
      * commits.csv
      * activity_month_of_year.csv
    * GitRepo1  
      * general.csv
      * authors.csv
      * commits.csv
      * activity_month_of_year.csv
    * GitRepon  
      * general.csv
      * authors.csv
      * commits.csv
      * activity_month_of_year.csv
  * projet2  
    * p2repo1  
      * general.csv
      * authors.csv
      * commits.csv
      * activity_month_of_year.csv
    * p2repo2  
      * general.csv
      * authors.csv
      * commits.csv
      * activity_month_of_year.csv
    