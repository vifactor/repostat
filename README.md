# [repostat](https://github.com/vifactor/repostat)

Modernized forked [gitstats](https://github.com/hoxu/gitstats) tool:
 - some visualizations added, plots and tables improved
 - code refactored by using Jinja templates
 - git output text parsing replaced with pygit2 library calls 
 - added "About" page

# Install
### Local version can be installed running
```bash
sudo python3 setup.py install [--record files.txt]
```

### Local develop version can be uninstalled running
```bash
sudo cat files.txt | sudo xargs rm -rf
```
if previously option "--record files.txt" was used at previous installation.

___
## gitstats Usage
**Sample:**
```bash
repo_stat [-h] [--project_name PROJECT_NAME]
                 [--output_format {html,csv}] [--append_csv] [--version]
                 [--config_file CONFIG_FILE]
                 git_repo output_path
```


### Args
#### output_format
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

#### append_csv
Default value: **false**  
This option used when output_format = csv.  
With append_csv = true option, the script will append target csv file if exists.

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

```bash
export_repos [-h] [--pull_repos] [--append_csv] project_folder output_folder
```

### Args
#### pull_repos
Execute git pull command in git repo folder before export statistics, and make repo up to date.

#### append_csv
Append exists csv, instead of rewrite. The repo statistics detail types exported to same files. 
This reduce the amount of created csv file.

#### project_folder
root folder location. This folder contain the project folders, and the project folder contain the project repositories.

#### output_folder structure without append_csv option
The script create same folder structure in the output folder as root-folder.  
The repos folders will contain the csv export files.

* root  
  * project1  
    * GitRepo  
      * general.csv
      * authors.csv
      * commits.csv
      * activity_month_of_year.csv
      * total_history.csv
    * GitRepo1  
      * general.csv
      * authors.csv
      * commits.csv
      * activity_month_of_year.csv
      * total_history.csv
    * GitRepon  
      * general.csv
      * authors.csv
      * commits.csv
      * activity_month_of_year.csv
      * total_history.csv
  * project2  
    * p2repo1  
      * general.csv
      * authors.csv
      * commits.csv
      * activity_month_of_year.csv
      * total_history.csv
    * p2repo2  
      * general.csv
      * authors.csv
      * commits.csv
      * activity_month_of_year.csv
      * total_history.csv

With **append_csv** option the repo details will be exported to the same csv files without the different ones in output folder structure.
The 5 csv file will be appear (general.csv, authors.csv, commits.csv, activity_month_of_year.csv, otal_history.csv) and contains all repo details.
