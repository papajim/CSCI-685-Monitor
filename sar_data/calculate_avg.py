#!/usr/bin/env python

import sys

f = open(sys.argv[1], "r")
lines = f.readlines()
f.close()

total = 0
_min = 100
_max = 0
for line in lines[1:]:
    split = line.replace("\n", "").split()
    split[0:2] =  [" ".join(split[0:2])]
    m = float(split[1])
    if m < _min:
        _min = m
    if m > _max:
        _max = m
    total += m

print _min
print total/(len(lines) - 1)
print _max

    
