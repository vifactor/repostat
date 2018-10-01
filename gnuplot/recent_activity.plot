set terminal pngcairo transparent size 1000,240
set size 1.0,1.0

set loadpath data_folder
set output 'recent_activity.png'
unset key
set xrange [-1:] reverse
set yrange [0:]
# FIXME: automatically estimate right xtics value range
set xtics 0,1,32 scale 0
set grid y
set ylabel "Commits"
set xlabel "Weeks ago"
plot 'recent_activity.dat' using 1:2:(0.7) w boxes fs solid, \
        'recent_activity.dat' using 1:2:(sprintf("%.0f",$2)) with labels font ",9" center offset 0,0.5 notitle
