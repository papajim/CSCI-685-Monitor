#!/usr/bin/env bash

jpeg="mem_usage_balanced_read.jpg"

gnuplot<<EOC
    reset
    set terminal jpeg size 1024,768 font "Calibri, 18"
    set output "$jpeg"
    set title "Memory Usage - Running YCSB Workload C"
    set xlabel "Time"
    set ylabel "Utilization (%)"
    set xdata time
    set timefmt "%s"
    set key left top
    plot "read_1.log" using 1:3 with lines lw 2 lt 3 title "memcached 1",\
         "read_2.log" using 1:3 with lines lw 2 lt 1 title "memcached 2"
EOC
