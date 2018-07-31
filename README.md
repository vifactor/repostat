# gitstats
Forked gitstats: git history statistics analizer

The idea is to modernize the existing tool:
 - refactor by using Jinja templates
 - replace self-made calls to git with calls to either PythonGit or pygit2 libraries
 - embed good-looking bokeh graphs instead of gnuplot ones
