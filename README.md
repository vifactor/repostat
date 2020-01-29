# [repostat](https://github.com/vifactor/repostat)

Git repository analysis report generator:
 - Python3 - compatible
 - removed redundancy in plots and tables
 - a couple of visualizations added and some improved
 - code cleaned up (e.g. [Jinja2](https://jinja.palletsprojects.com/en/2.10.x/)
  used for html generation)
 - git output text parsing replaced with pygit2 library calls

Enhanced fork of [gitstats](https://github.com/hoxu/gitstats) tool.

## Ubuntu installation
### Using pip (recommended)
```bash
sudo pip3 install git+https://github.com/vifactor/repostat
```
This installation procedure may require manual installation 
of required dependencies, e.g. libgit2, gnuplot. But should also
work in other non-Debian Linux distributions.

### Using ppa (discontinued)
```bash
sudo add-apt-repository ppa:vifactor/ppa
sudo apt update
sudo apt install repostat
```
**Currently only Ubuntu 18.04 is supported**

## Windows installation
Check issue #57

___
## Scripts
### repostat
**Usage**
```bash
repostat [--help] [--version] [--config_file CONFIG_FILE]
                 git_repository_path output_path
```
See "--help" for details.

## Additional features

### Mailmap
Starting from v1.1.2+ repostat supports [git mailmap](https://git-scm.com/docs/git-check-mailmap). 
Two things are required in order to make the feature working:
- install pygit2 v.0.28+
- create and fill .mailmap file (e.g. in the root of your repository)

*Note: even Ubuntu 19.10 has libgit2 v.0.27.x in its repositories,
so it means mailmap will not work there by default. Please, install
[newer versions](https://www.pygit2.org/install.html) (v.0.28+)
of libgit2 + pygit2 to enable the feature.*

### Relocatable reports
By default, images, css- and js-files required to for html report
rendering do not get copied to report directory. Html pages contain 
absolute paths to assets located in repostat installed package.

Starting from v.1.0.x, the *--copy-assets* command-line option forces
program to copy assets to generated report and embed relative paths
in html-files (see #74)

### Tags rendering
Some git repositories contain thousands of tags most of which are not 
worth to check. Since v.1.3.0 there is a possibility to limit number 
of tags displayed in "Tags" tab of the HTML report or even hide the tab.
The feature is controlled by "max_recent_tags" field in JSON 
file fed into script as follows:
```
repostat --config-file <path_to_config.json> <repo_path> <out_path>
```
If JSON file has following content `{ [...], "max_recent_tags": 8 }`,
the report will contain 8 most recent tags in "Tags" page. Setting the
field `max_recent_tags` to zero will not render "Tags" page at all. If
no such field provided in JSON settings, report will contain "Tags" page
with all tags in the analysed repository.
