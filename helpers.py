import pika
import urlparse
import urllib
import ssl

def amqp_connect(amqp_details):
    creds = pika.PlainCredentials(amqp_details["username"], amqp_details["password"])
    parameters = pika.ConnectionParameters(host=amqp_details["hostname"],
                                           port=amqp_details["port"],
                                           ssl=amqp_details["ssl"],
                                           ssl_options={"cert_reqs": ssl.CERT_NONE},
                                           virtual_host=amqp_details["virtual_host"],
                                           credentials=creds)
    return pika.BlockingConnection(parameters)
