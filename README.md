# [repostat](https://github.com/vifactor/repostat)
Python3-compatible Git repository analyser and HTML-report generator 
with [nvd3](http://nvd3.org/) -driven interactive metrics visualisations.

**May not work with Python 3.9+!** See https://github.com/vifactor/repostat/issues/198

Initially, a fork of [gitstats](https://github.com/hoxu/gitstats) tool.

---
Check how a *repostat*'s report looks like by going to:

https://repostat.imfast.io/


## Installation
Starting from v2.0.0, *repostat* is installable from [PyPi](https://pypi.org/project/repostat-app/)
under the name *repostat-app*. Installation should be as simple as:
```bash
pip3 install repostat-app
```
#### Newest and older versions
- To install a development version with newest changes from
[*repostat*'s github repository](https://github.com/vifactor/repostat),
the following command may be executed:
    ```bash
    sudo pip3 install git+https://github.com/vifactor/repostat
    ```
    This command installs *repostat* from HEAD of `master` branch.

- To install *repostat* at specific tag or branch, use the following syntax
    ```bash
    sudo pip3 install git+https://github.com/vifactor/repostat@<branch|tag>
    ```
*NOTE:*
Versions prior to v2.0.0 have additional system-dependencies, e.g.
`gnuplot`.

### OS-specific requirements

#### Linux installation
![Repostat for Ubuntu 20.04](https://github.com/vifactor/repostat/workflows/Repostat%20for%20Ubuntu%2020.04/badge.svg)

`python3-pip` must be in the system and then installation via `pip`
works fine.

#### Mac OS (Catalina) installation
![Repostat for Mac OS](https://github.com/vifactor/repostat/workflows/Repostat%20for%20Mac%20OS/badge.svg)

Prior to installing repostat one needs to make sure to have
*right version* of libgit2 in the system. This can be achieved
- following [pygit2 installation](https://www.pygit2.org/install.html#id13) instructions
- (not recommended) installing it via Homebrew
```bash
$ brew update
$ brew install libgit2
```
Then, install *repostat* via:
```
$ pip3 install repostat-app
```

*NOTE*:
1) Homebrew-way to install packages is slow and may break system dependencies.
2) repostat's [CI for OSX](https://github.com/vifactor/repostat/blob/master/.github/workflows/repostat_macos.yml)
builds libgit2 from source.

### Windows installation
![Repostat for Windows](https://github.com/vifactor/repostat/workflows/Repostat%20for%20Windows%202019/badge.svg)

Once there is python v3.6+ in the system path, *repostat* can be installed via:
```shell script
python -m pip install repostat-app
```

*NOTE*: On Windows 10+, symlink to `general.html` is not generated, when
*repostat* launched by an unprivileged user. 
___
## Usage
```bash
repostat [--help] [--version] [--config_file CONFIG_FILE_PATH]
                 git_repository_path report_output_path
```
Run `repostat --help` for details.

### Configuration file

A report can be customized using a JSON settings file. The file is passed
using the `--config-file` option as follows:

```
repostat --config-file <path_to_config.json> <repo_path> <out_path>
```
Configuration file might contain following fields (all are optional):
```json
{
    "max_domains": 10,
    "max_authors": 7,
    "max_plot_authors_count": 10,
    "max_authors_of_months": 6,
    "authors_top": 5,
    "colormap": "classic",
    "max_recent_tags": -1,
    "orphaned_extension_count": 2,
    "time_sampling": "W"
}
```
Detailed information about role of the fields is below.

#### Authors page configuration

These values are usually adjusted to accommodate projects with various number
of contributors and activity levels, to avoid showing too much or too little
information.

* `max_domains`: number of e-mail domains to show in author stats
* `max_authors`: number of authors in the "top authors" table 
(other authors are listed without detailed stats)
* `max_plot_authors_count`: number of authors to include in plots
in "Authors"-page (rest of the authors will be grouped as "Others"). 
* `max_authors_of_months`: number of months for which "author of 
the month" should be displayed
* `authors_top`: number of authors to show for each month/year in the
author of month/year list
* `orphaned_extension_count`: max file extension count to be 
considered as `orphaned` and displayed in report in the corresponding
category (default: 0, i.e. all extensions are displayed)

#### Colorscheme configuration

The colors of the thread "heat maps" tables in the activity page can be customized
using the "colormap" option. The allowed values are:

* `classic`: (default) uses shades of red only, like gitstats
* `plasma`: uses the ["plasma" colormap](https://bids.github.io/colormap/)
* `viridis`: uses the ["viridis" colormap](https://bids.github.io/colormap/)
* `clrscc`: uses a selection of colors from https://clrs.cc/

#### History plots sampling
is controlled by `"time_sampling"` field in configuration file and
defines how timeseries , e.g. number of files over a
repository history, are sampled. By default, weekly-sampling is used.
For old repositories one might want to increase that value to
month or even quarter.
Accepted values for `"time_sampling"` are the [Pandas' Offset aliases](https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases)

#### Tags rendering

Some git repositories contain thousands of tags most of which are not 
worth to check. Since v.1.3.0 there is a possibility to limit the number 
of tags displayed in "Tags" tab of the HTML report or even hide the tab.

The feature is controlled by "max_recent_tags" field

If JSON file has following content `{ [...], "max_recent_tags": 8 }`,
the report will contain the 8 most recent tags in "Tags" page. Setting the
field `max_recent_tags` to zero will not render "Tags" page at all. If
no such field is provided in JSON settings, the report will contain a "Tags"
page with all tags in the analysed repository.

### Additional features

#### Mailmap
Starting from v1.1.2+ repostat supports [git mailmap](https://git-scm.com/docs/git-check-mailmap). 
Two things are required in order to make the feature working:
- have pygit2 v.0.28+ installed
- create and fill .mailmap file (e.g. in the root of your repository)

#### Relocatable reports
By default, images, css- and js-files required for html report
rendering do not get copied to a report directory. Html pages contain 
absolute paths to assets located in *repostat*'s package installation
directory.

Starting from v.1.0.x, the `--copy-assets` command-line option forces
program to copy assets to generated report and embed relative paths
in the generated html-files.

## How to contribute

Bug reports and feature requests as well as pull requests are welcome.
Please, check the ["Issues"](https://github.com/vifactor/repostat/issues)
on github to find something you would like to work on.
