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
python3 gitstats -coutput=[csv,html] -cproject_name=ProjectNameSample [git-repo-folder] [output-folder]
```


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

```bash
python export_repos.py [root-folder] [output-folder]
```

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
