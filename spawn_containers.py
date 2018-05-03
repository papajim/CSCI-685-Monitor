#!/usr/bin/env python

import json
import docker
import threading
from monitor import monitor

threadArray = []

with open("config.json", "r") as f:
    config = json.load(f)


client = docker.DockerClient(base_url = "tcp://192.168.88.13:8081", version = "1.37")

containers = []

for k in xrange(len(config["containers"])):
    containers.append(client.containers.run(image=config["containers"][k]["image"], command=config["containers"][k]["cmd"], detach=True, auto_remove=True))

for i in xrange(len(containers)):
    thread = threading.Thread(name="#"+str(i), target=monitor, args=[containers[i]])
    threadArray.append(thread)
    thread.start()

for thread in threadArray:
    thread.join()

for container in containers:
    container.stop()
