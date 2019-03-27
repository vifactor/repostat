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