#!/usr/bin/env python

import docker
import time
import json

def calculateCPUPercent(stats):
    cpuPercent = 0.0

    previousCPU = float(stats["precpu_stats"]["cpu_usage"]["total_usage"])
    currentCPU = float(stats["cpu_stats"]["cpu_usage"]["total_usage"])
    previousSystem = float(stats["precpu_stats"]["system_cpu_usage"])
    currentSystem = float(stats["cpu_stats"]["system_cpu_usage"])
    
    cpuDelta = currentCPU - previousCPU
    systemDelta = currentSystem - previousSystem

    onlineCPUs  = float(stats["cpu_stats"]["online_cpus"])

    if onlineCPUs == 0.0:
        onlineCPUs = float(len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"]))

    if systemDelta > 0.0 and cpuDelta > 0.0:
        #cpuPercent = (cpuDelta / systemDelta) * onlineCPUs * 100.0
        cpuPercent = (cpuDelta / systemDelta) * 100.0

    return cpuPercent

#client = docker.DockerClient(base_url = "tcp://192.168.88.13:8081", version = "1.37")

#print client.version()
#container = client.containers.run(image="stress", command="stress -c 2", detach=True, auto_remove=True)

#for i in xrange(10):
#    stats = container.stats(stream=False)
#    print calculateCPUPercent(stats)
#    #time.sleep(2)

#container.stop()
#print client.containers.list()

def monitor(container):
    for i in xrange(10):
        start = time.time()
        stats = container.stats(stream=False)
        cpu_usage = calculateCPUPercent(stats)
        end = time.time()
        
        print end - start
        print json.dumps(cpu_usage, indent=2)
