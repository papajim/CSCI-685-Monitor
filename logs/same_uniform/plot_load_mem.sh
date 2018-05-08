#!/usr/bin/env bash

jpeg="mem_usage_balanced.jpg"

gnuplot<<EOC
    reset
    set terminal jpeg size 1024,768 font "Calibri, 18"
    set output "$jpeg"
    set title "Memory Usage - Loading YCSB Workload A"
    set xlabel "Time"
    set ylabel "Utilization (%)"
    set xdata time
    set timefmt "%s"
    set key left top
    plot "load_1.log" using 1:3 with lines lw 2 lt 3 title "memcached 1",\
         "load_2.log" using 1:3 with lines lw 2 lt 1 title "memcached 2"
EOC
