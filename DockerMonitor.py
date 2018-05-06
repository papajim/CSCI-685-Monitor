#!/usr/bin/env python

import sys
import signal
import docker
import time
import json


class DockerMonitor:
    def __init__(self, docker_hostname, container, cpu_limit, interval):
        self.is_stopped = False
        self.docker_hostname = docker_hostname
        self.container = container
        self.cpu_limit = cpu_limit
        self.interval = (inteval - 2) if interval > 2 else 0

    def stop_monitoring(self):
        self.is_stopped = True

    def calculateCPUPercent(self, stats):
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
            cpuPercent = (cpuDelta / systemDelta) * onlineCPUs / self.cpu_limit * 100.0
            #cpuPercent = (cpuDelta / systemDelta) * onlineCPUs * 100.0
            #cpuPercent = (cpuDelta / systemDelta) * 100.0

        return cpuPercent

    def start(self):
        monitor_event = {}
        monitor_event["hostname"] = self.docker_hostname
        monitor_event["container_id"] = self.container.id
        
        while True:
            stats = self.container.stats(stream=False)
            cpu_usage = self.calculateCPUPercent(stats)
        
            monitor_event["timestamp"] = time.time()
            monitor_event["cpu_usage"] = cpu_usage

            print json.dumps(monitor_event, indent=2)

            if self.is_stopped:
                sys.exit(0)
