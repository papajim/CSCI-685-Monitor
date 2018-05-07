#!/usr/bin/env python

import os
import sys
import json
import signal
import logging
import optparse
from helpers import amqp_connect

# --- global variables ----------------------------------------------------------------
message_count = 0
amqp_conn = None
amqp_channel = None

instances = {}

prog_base = os.path.split(sys.argv[0])[1]   # Name of this program
logger = logging.getLogger("my_logger")

# --- functions ----------------------------------------------------------------------
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
    
    for i in instances:
        if instances[i]["counter"] > 0:
            write_stats_to_file(i)

    if not amqp_conn is None:
        amqp_conn.close()


def write_stats_to_file(container_id):
    with open("logs/"+container_id[:12]+'.log', "a+") as g:
        for m in instances[container_id]["measurements"]:
            output = "%d    %f    %f    %d     %d     %d    %d\n" % (m["end_timestamp"], m["cpu_usage"], m["memory_usage_percent"], m["blkio"]["bytes_read"], m["blkio"]["bytes_write"], m["network"]["rx_bytes"],m["network"]["tx_bytes"])
            g.write(output)

    instances[container_id]["counter"] = 0
    instances[container_id]["measurements"] = []


def on_message(method_frame, header_frame, body):
    parsed = json.loads(body)
    container_id = parsed["container_id"]
    if container_id in instances:
        instances[container_id]["counter"] += 1
        instances[container_id]["measurements"].append(parsed)
        if instances[container_id]["counter"] >= 10:
            write_stats_to_file(container_id)
    else:
        instances[container_id] = {}
        instances[container_id]["counter"] = 1
        instances[container_id]["measurements"] = [parsed]

    #print json.dumps(parsed, indent=2)
    #amqp_channel.basic_ack(delivery_tag=method_frame.delivery_tag)
    

def setup_amqp(amqp_details):
    global amqp_conn
    global amqp_channel
    global amqp_queue

    amqp_conn = amqp_connect(amqp_details)
    amqp_channel = amqp_conn.channel()
    #amqp_channel.basic_consume(on_message, amqp_details["queue"])
    
    return


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

    setup_amqp(config["amqp_endpoint"])

    try:
        for measurement in amqp_channel.consume(config["amqp_endpoint"]["queue"], no_ack=True, inactivity_timeout=60.0):
            if measurement:
                method_frame, header_frame, body = measurement
                on_message(method_frame, header_frame, body)
    
    except Exception as e:
        logging.critical(e)
        for i in instances:
            if instances[i]["counter"] > 0:
                write_stats_to_file(i)

        if not amqp_conn is None:
            amqp_conn.close()


if __name__ == "__main__":
    main()
    
