#!/usr/bin/env python

import sys
import signal
import docker
import time
import json


class DockerMonitor:
    def __init__(self, stats_queue, docker_hostname, container, cpu_limit, interval):
        self.is_stopped = False
        self.docker_hostname = docker_hostname
        self.container = container
        self.cpu_limit = cpu_limit
        self.stats_queue = stats_queue
        self.interval = interval if interval > 2 else 0

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

        if systemDelta > 0.0 and cpuDelta > 0.0 and self.cpu_limit > 0:
            cpuPercent = (cpuDelta / systemDelta) * onlineCPUs / self.cpu_limit * 100.0
        elif systemDelta > 0.0 and cpuDelta > 0.0:
            cpuPercent = (cpuDelta / systemDelta) * 100.0
            #cpuPercent = (cpuDelta / systemDelta) * onlineCPUs * 100.0
            #cpuPercent = (cpuDelta / systemDelta) * 100.0

        return cpuPercent
    
    def calculateBlockIO(self, stats):
        blkRead = 0
        blkWrite = 0

        for entry in stats["blkio_stats"]["io_service_bytes_recursive"]:
            op = entry["op"].lower()
            if op == "read":
                blkRead += entry["value"]
            elif op == "write":
                blkWrite += entry["value"]

        return (blkRead, blkWrite)


    def calculateNetwork(self, stats):
        netRx = 0
        netTx = 0

        for iface in stats["networks"]:
            netRx += float(stats["networks"][iface]["rx_bytes"])
            netTx += float(stats["networks"][iface]["tx_bytes"])

        return (netRx, netTx)

    def start(self):
        monitor_event = {}
        monitor_event["hostname"] = self.docker_hostname
        monitor_event["container_id"] = self.container.id
        monitor_event["cpu_usage"] = 0.0
        monitor_event["memory_limit"] = 0
        monitor_event["memory_usage"] = 0
        monitor_event["memory_usage_percent"] = 0
        monitor_event["blkio"] = {}
        monitor_event["blkio"]["bytes_read"] = 0
        monitor_event["blkio"]["bytes_write"] = 0
        monitor_event["blkio"]["read_delta"] = 0
        monitor_event["blkio"]["write_delta"] = 0
        monitor_event["network"] = {}
        monitor_event["network"]["rx_bytes"] = 0
        monitor_event["network"]["tx_bytes"] = 0
        monitor_event["network"]["rx_delta"] = 0
        monitor_event["network"]["tx_delta"] = 0
        
        k = 0
        start_time = time.time()
        while True:
            k += 1
            stats = self.container.stats(stream=False)
            cpu_usage = self.calculateCPUPercent(stats)
            monitor_event["cpu_usage"] += cpu_usage
            monitor_event["memory_usage"] += stats["memory_stats"]["usage"]

            if round(time.time() - start_time) >= self.interval:
                monitor_event["start_timestamp"] = int(start_time)
                monitor_event["end_timestamp"] = int(time.time())
                monitor_event["cpu_usage"] = round(monitor_event["cpu_usage"] / k*1.0, 2)
                monitor_event["memory_usage"] = round(monitor_event["memory_usage"] / k*1.0, 2)
                monitor_event["memory_limit"] = stats["memory_stats"]["limit"]
                monitor_event["memory_usage_percent"] = round(monitor_event["memory_usage"] / monitor_event["memory_limit"] * 100.0, 2)
                
                (blkRead, blkWrite) = self.calculateBlockIO(stats)
                monitor_event["blkio"]["read_delta"] = blkRead - monitor_event["blkio"]["bytes_read"]
                monitor_event["blkio"]["write_delta"] = blkWrite - monitor_event["blkio"]["bytes_write"]
                monitor_event["blkio"]["bytes_read"] = blkRead
                monitor_event["blkio"]["bytes_write"] = blkWrite
                
                (netRx, netTx) = self.calculateNetwork(stats)
                monitor_event["network"]["rx_delta"] = netRx - monitor_event["network"]["rx_bytes"]
                monitor_event["network"]["tx_delta"] = netTx - monitor_event["network"]["tx_bytes"]
                monitor_event["network"]["rx_bytes"] = netRx
                monitor_event["network"]["tx_bytes"] = netTx

                #print json.dumps(monitor_event, indent=2)
                self.stats_queue.put(json.dumps(monitor_event))
                k = 0
                start_time = time.time()
                monitor_event["cpu_usage"] = 0
                monitor_event["memory_usage"] = 0

            if self.is_stopped:
                sys.exit(0)
