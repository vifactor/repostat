set terminal pngcairo transparent size 640,240
set size 1.0,1.0

set loadpath data_folder
set output 'files_by_date.png'
unset key
set xdata time
set timefmt "%s"
set format x "%Y-%m"
set yrange [0:]
set y2range [0:]
set ylabel "Files"
set y2label "Lines"
set xtics rotate
set ytics autofreq
set y2tics autofreq
set key left top

plot 'files_by_date.dat' using 1:2 w steps lw 2 title "Files count", \
 'lines_of_code.dat' using 1:2 w lines lw 2 axes x1y2 title "Lines count"
