2.2.0 (2020-06-26)
-------------------------
- Group together orphaned extensions using "orphaned_extension_count"-config
- Add new metrics: "Top knowledge carriers", "lost knowledge", etc
- Do not display lines count for binary files in extension distribution table
- Add console progress bar when fetching history data
- Minor formatting changes

2.1.3 (2020-06-13)
-------------------------
- Fix erroneous AoY and AoM commits count (reported in some cases)
- Fix crash when --contribution option if passed and "Others" category needs to be appended
- Add console progress bar when blame data is fetched
- Report execution time of raws data fetching in nicer format

2.1.2 (2020-05-23)
-------------------------
- Do not fetch blame data if no "--contribution" option was passed (#177)
- Process tags data using pandas
- "Improve" tags visualization

2.1.1 (2020-05-17)
-------------------------
- Fetch blame data in many threads
- Process revision data using pandas
- Improve file types grouping
- Change way to list *repostat*'s authors (all authors are not in `release_data.json`)
- Fix required python version for packaging (3.6+)
- Minor improvements, e.g. display of pygit2 version

2.1.0 (2020-05-05)
-------------------------
- Added contribution pie-chart (instead of column in top authors table)
- Decoupled limits on number of authors in plots and in top authors table
- Added merge commits statistics
- Introduce --with-index-page option to generate index.html
- Minor visual changes on General- and Authors-pages
- Code refactoring

2.0.2 (2020-04-30)
-------------------------
- Fix Windows crash due to symlink creation by an unprivileged user

2.0.1 (2020-04-25)
-------------------------
- Provide configuration option to adjust time-sampling
- Use unmapped author's email in domains distribution
- Improve current year activity inset plot

2.0.0 (2020-04-18)
-------------------------
- replace gnuplot graphs with interactive nvd3-plots
- use pandas to process git raw data 

1.3.1 (2020-02-11)
-------------------------
- "Restore "authors per year/month" count in tables
- Prevent creation of index.html symlink if exists
- Remove dev-files from git-archive
