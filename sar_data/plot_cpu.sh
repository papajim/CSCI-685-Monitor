#!/usr/bin/env bash

jpeg="cpu_usage.jpg"

gnuplot<<EOC
    reset
    set terminal jpeg size 1024,768 font "Calibri, 18"
    set output "$jpeg"
    set title "CPU usage"
    set style data histogram
    set style histogram cluster gap 1
    set style fill solid border -1
    set boxwidth 0.9
    set ylabel "Usage (%)"
    set xlabel "Containers Monitored"
    plot "cpu_usage_min_avg_max.out" using 3:xtic(2) title "Min", '' u 4 title "Avg", '' u 5 title "Max"
EOC
