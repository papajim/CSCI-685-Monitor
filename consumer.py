#!/usr/bin/env python

import os
import sys
import json
import signal
from helpers import amqp_connect

# --- global variables ----------------------------------------------------------------
message_count = 0
amqp_conn = None
amqp_channel = None
amqp_exchange = None
amqp_routing_key = None

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
    
    if not amqp_conn is None:
        amqp_conn.close()


def setup_amqp(amqp_details):
    global amqp_conn
    global amqp_channel
    global amqp_exchange
    global amqp_routing_key

    EXCH_OPTS = {'exchange_type' : 'topic', 'durable' : True, 'auto_delete' : False}
    
    amqp_conn = amqp_connect(amqp_details)
    amqp_channel = amqp_conn.channel()
    amqp_channel.exchange_declare(amqp_details["exchange"], **EXCH_OPTS)

    amqp_exchange = amqp_details["exchange"]
    amqp_routing_key = amqp_details["routing_key"]
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

    print config

if __name__ == "__main__":
    main()
    
