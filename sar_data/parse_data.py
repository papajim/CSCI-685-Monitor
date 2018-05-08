#!/usr/bin/env python

import sys

if len(sys.argv) < 5:
    raise Exception("Usage: %s input_file output_file start_filter end_filter" % sys.argv[0])

f = open(sys.argv[1], "r")
lines = f.readlines()
f.close()

g = open(sys.argv[2], "w+")
g.write("#timestamp\ttotal_cpu\n")

for line in lines[3:]:
    split = line.replace("\n", "").split()
    split[0:2] =  [" ".join(split[0:2])]

    if split[0] > sys.argv[3] and split[0] < sys.argv[4]:
        total_cpu = 100.0 - float(split[7])
        g.write("%s %.2f\n"%(split[0], total_cpu))

g.close()
    
