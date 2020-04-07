# [repostat](https://github.com/vifactor/repostat)
[![Build Status](https://travis-ci.org/vifactor/repostat.svg?branch=master)](https://travis-ci.org/vifactor/repostat)

Git repository analysis report generator:
 - Python3 - compatible
 - removed redundancy in plots and tables
 - a couple of visualizations added and some improved
 - code cleaned up (e.g. [Jinja2](https://jinja.palletsprojects.com/en/2.10.x/)
  used for html generation)
 - git output text parsing replaced with pygit2 library calls
 - statistics calculation is done via Pandas

Enhanced fork of [gitstats](https://github.com/hoxu/gitstats) tool.

## Installation
There are currently two versions maintained. Stable version is in
branch `v1.3.x`, while development (future v2.x.x) version is on `master`.

### Linux installation (Ubuntu 18.04 checked)
```bash
sudo apt install gnuplot
sudo pip3 install git+https://github.com/vifactor/repostat
```
This command installs *repostat* from HEAD of `master` branch. To install
*repostat* at specific tag or branch, use the following syntax
```bash
sudo pip3 install git+https://github.com/vifactor/repostat@<branch|tag>
```
![Repostat for Ubuntu 18.04](https://github.com/vifactor/repostat/workflows/Repostat%20for%20Ubuntu%2018.04/badge.svg)

### Mac OS (Catalina) installation
```bash
$ brew update
$ brew install libgit2
$ brew install gnuplot

$ pip3 install git+https://github.com/vifactor/repostat
```
NOTE: Homebrew-way to install packages is slow and may break system dependencies.
Please, check [pygit2 installation instructions](https://www.pygit2.org/install.html#id13)
or current [CI setup](https://github.com/vifactor/repostat/blob/master/.github/workflows/repostat_macos.yml):

![Repostat for Mac OS](https://github.com/vifactor/repostat/workflows/Repostat%20for%20Mac%20OS/badge.svg)


### Windows installation
Check [issue #57](https://github.com/vifactor/repostat/issues/57)
___
## Usage
```bash
repostat [--help] [--version] [--config_file CONFIG_FILE]
                 git_repository_path report_output_path
```
Run `repostat --help` for details.

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

## Configuration file

The report can be customized using a JSON settings file. The file is passed
using the --config-file option as follows:

```
repostat --config-file <path_to_config.json> <repo_path> <out_path>
```

### Authors page configuration

These values are usually adjusted to accomodate projects with various number
of contributors and activity levels, to avoid showing too much or too little
information.

* max_domains: number of e-mail domains to show in author stats
* max_ext_length
* max_authors: number of authors in the "top authors" table (other authors are
	listed without detailed stats)
* max_authors_of_months: number of months for which "author of the month" should be displayed
* authors_top: number of authors to show for each month in the author of month/year list

### Colorscheme configuration

The colors of the thread "heat maps" tables in the activity page can be customized
using the "colormap" option. The allowed values are:

* classic: uses shades of red only, like gitstats. This is the default if the option is not specified.
* plasma: uses the "plasma" colormap as described [here](https://bids.github.io/colormap/)
* viridis: uses the "viridis" colormap as described [here](https://bids.github.io/colormap/)
* clrscc: uses a selection of colors from [https://clrs.cc/]

### Tags rendering

Some git repositories contain thousands of tags most of which are not 
worth to check. Since v.1.3.0 there is a possibility to limit the number 
of tags displayed in "Tags" tab of the HTML report or even hide the tab.

The feature is controlled by "max_recent_tags" field

If JSON file has following content `{ [...], "max_recent_tags": 8 }`,
the report will contain the 8 most recent tags in "Tags" page. Setting the
field `max_recent_tags` to zero will not render "Tags" page at all. If
no such field is provided in JSON settings, the report will contain a "Tags"
page with all tags in the analysed repository.

## How to contribute

Bug reports and feature requests as well as pull requests are welcome.
Please, check the "Issues" on github to find something you would like
to work on.

### Debian packaging
There was some work done to prepare Debian package of *repostat*. The packaging
code can still be found on `debian/master` branch in this repository. 
Instructions (incomplete and outdated) on how to package using
[gbp](http://honk.sigxcpu.org/projects/git-buildpackage/manual-html/gbp.html)
are [in wiki](https://github.com/vifactor/repostat/wiki/Packaging-notes).

### Snap package
Incomplete and outdated `snapcraft.yaml` file is in `snapcraft` branch.
