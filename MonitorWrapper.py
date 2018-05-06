#!/usr/bin/env python

import time
import os
import sys
import signal
import json
import docker
import threading
import optparse
import logging
import Queue
from DockerMonitor import DockerMonitor

# --- global variables ----------------------------------------------------------------
containers = []
threadArray = []
dockerMonitors = []

prog_base = os.path.split(sys.argv[0])[1]   # Name of this program
logger = logging.getLogger("my_logger")
# --- functions ----------------------------------------------------------------
            
def setup_logger(debug_flag):
    # log to the console
    console = logging.StreamHandler()
    
    # default log level - make logger/console match
    logger.setLevel(logging.INFO)
    console.setLevel(logging.INFO)

    # debug - from command line
    if debug_flag:
        logger.setLevel(logging.DEBUG)
        console.setLevel(logging.DEBUG)

    # formatter
    formatter = logging.Formatter("%(asctime)s %(levelname)7s:  %(message)s")
    console.setFormatter(formatter)
    logger.addHandler(console)
    logger.debug("Logger has been configured")


def prog_sigint_handler(signum, frame):
    logger.warn("Exiting due to signal %d" % (signum))
    for monitor in dockerMonitors:
        monitor.stop_monitoring()

    for thread in threadArray:
        thread.join()

    for container in containers:
        container.stop()

    sys.exit(1)

def publishStats(stats_object):
    print json.dumps(stats_object, indent=2)
    return

def listenForStats(stats_queue):
    while True:
        try:
            stats_object = stats_queue.get(timeout=30)
        except Queue.Empty as e:
            continue
        publishStats(stats_object)

def runMonitor(stats_queue, docker_hostname, container, cpu_limit, interval=2):
    monitor = DockerMonitor(stats_queue, docker_hostname, container, cpu_limit, interval)
    dockerMonitors.append(monitor)
    monitor.start()

def main():
    # Configure command line option parser
    prog_usage = "usage: %s [options]" % (prog_base)
    parser = optparse.OptionParser(usage=prog_usage)
    parser.add_option("-f", "--file", action = "store", dest = "file", help = "Config file")
    parser.add_option("-d", "--debug", action = "store_true", dest = "debug", help = "Enables debugging output")

    # Parse command line options
    (options, args) = parser.parse_args()
    setup_logger(options.debug)

    if not options.file:
        logger.critical("An input file has to be given with --file")
        sys.exit(1)

    # Die nicely when asked to (Ctrl+C, system shutdown)
    signal.signal(signal.SIGINT, prog_sigint_handler)
    signal.signal(signal.SIGTERM, prog_sigint_handler)

    with open(options.file, "r") as f:
        config = json.load(f)

    docker_hostname = config["docker"]["hostname"]
    docker_port = config["docker"]["port"]
    docker_version = config["docker"]["version"]

    #client = docker.DockerClient(base_url = "tcp://192.168.88.13:8081", version = "1.37")
    client = docker.DockerClient(base_url = "tcp://" + docker_hostname + ":" + docker_port, version = docker_version)

    stats_queue = Queue.Queue()

    for k in xrange(len(config["containers"])):
        cpu_limit = 0
        interval = 0
        if "cpu_limit" in config["containers"][k]:
            cpu_limit = config["containers"][k]["cpu_limit"]

        if "interval" in config["containers"][k]:
            interval = config["containers"][k]["interval"]
        
        logger.info("Starting up container image %s with command \"%s\", cpu_limit %d and interval %d" % (config["containers"][k]["image"], config["containers"][k]["cmd"], cpu_limit, interval))
        container = client.containers.run(image=config["containers"][k]["image"], command=config["containers"][k]["cmd"], detach=True, auto_remove=True)
        containers.append(container)

        thread = threading.Thread(name="#"+str(k), target=runMonitor, args=(stats_queue, docker_hostname, container, cpu_limit, interval,))
        threadArray.append(thread)
        thread.start()

    listenForStats(stats_queue)

    for thread in threadArray:
        thread.join()

    for container in containers:
        container.stop()

if __name__ == "__main__":
    main()
