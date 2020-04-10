set terminal png transparent size 640,240
set size 1.0,1.0

stats 'commits_by_author.dat' skip 1 nooutput
max_col = ceil(STATS_columns)

set terminal png transparent size 640,480
set output 'commits_by_author.png'
set key left top
set yrange [0:]
set xdata time
set timefmt "%Y-%m-%d"
set format x "%Y-%m"
set grid y
set ylabel "Commits"
set xtics rotate

plot for [i=2:(max_col)] 'commits_by_author.dat' using 1:(sum [col=i:(max_col)] column(col)) \
            title columnheader(i) with filledcurves x1
