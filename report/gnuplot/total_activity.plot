set terminal pngcairo transparent size 1000,340
set size 1.0,1.0

set loadpath data_folder
set output 'total_activity.png'

set multiplot
unset key
set xtics 1 rotate
set grid y
set ylabel "Commits"
set yrange [0:]
plot 'commits_by_year.dat' using 1:2:(0.9) w boxes fs solid

set origin .06, .54
set size .45,.45

set object rectangle from graph 0,0 to graph 1,1 behind fillcolor rgb 'white' fillstyle transparent solid 0.35 noborder

current_year = strftime("%Y", time(0))
first_month_of_year = current_year.'-01'
last_month_of_year = current_year.'-12'

unset xrange
set title "Commits in ".current_year font ", 11" offset 0, -1
set yrange [0:]
set ytics font ", 9"
set xdata time
set timefmt "%Y-%m"
set format x "%b"
set xtics 1 rotate
set xtics font ", 9"
set xtics first_month_of_year,2592000,last_month_of_year
set xrange [first_month_of_year:last_month_of_year]
set bmargin 2
set grid y
set ylabel "Commits" font ", 10" offset 2, 0
set boxwidth 0.7 relative
plot 'commits_by_year_month.dat' using 1:2 w boxes fs solid

unset multiplot
