# [repostat](https://github.com/vifactor/repostat)

Modernized forked [gitstats](https://github.com/hoxu/gitstats) tool:
 - port to Python 3
 - some visualizations added, plots and tables improved
 - code refactored by using Jinja templates
 - git output text parsing replaced with pygit2 library calls 
 - added "About" page

# Ubuntu installation
## Using pip
```bash
sudo pip3 install [-e] https://github.com/vifactor/repostat
```
This installation procedure may require manual installation 
of required dependencies, e.g. libgit2, gnuplot. But should also
work in other non-Debian Linux distributions.

## Using ppa
```bash
sudo add-apt-repository ppa:vifactor/ppa
sudo apt update
sudo apt install repostat
```
**Currently only Ubuntu 18.04 is supported**

# Windows installation
Check issue #57

___
# Scripts
## repostat
**Usage**
```bash
repostat [--help] [--version] [--config_file CONFIG_FILE]
                 git_repository_path output_path
```
See "--help" for details.