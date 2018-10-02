set terminal png transparent size 640,240
set size 1.0,1.0

stats 'lines_of_code_by_author.dat' skip 1 nooutput
max_col = STATS_columns

set terminal png transparent size 640,480
set output 'lines_of_code_by_author.png'
set key left top
set yrange [0:]
set xdata time
set timefmt "%s"
set format x "%Y-%m"
set grid y
set ylabel "Lines"
set xtics rotate

plot for [i=2:max_col] 'lines_of_code_by_author.dat' using 1:i with lines lw 2 title columnheader(i)
