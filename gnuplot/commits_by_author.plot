set terminal png transparent size 640,240
set size 1.0,1.0

stats 'commits_by_author.dat' skip 1 nooutput
max_col = STATS_columns

set terminal png transparent size 640,480
set output 'commits_by_author.png'
set key left top
set yrange [0:]
set xdata time
set timefmt "%s"
set format x "%Y-%m-%d"
set grid y
set ylabel "Commits"
set xtics rotate
set bmargin 6

set key autotitle columnheader

plot for [i=2:max_col] 'commits_by_author.dat' using 1:i with lines
