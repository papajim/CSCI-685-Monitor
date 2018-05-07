#!/usr/bin/env bash

./MonitorWrapper.py -f "$1" &

sleep 5m

kill $!
