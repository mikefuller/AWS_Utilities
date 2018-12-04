#!/usr/bin/env python
############################# DESCRIPTION ##############################
#
# Script will take a monthly inventory and compare it against the previous
# months inventory as well as the inventory listed in the SSP
#
# usage:  python InventoryCompare.py <past month inventory file> <new inventory>
#
# Note: the file containing the ssp inventory must be referenced in the
# ssp_inventory variable below
#
#-----------------------------------------------------------------------
# Deps. : Python 2.6+, boto 2.0
########################################################################

import boto,boto.ec2
import sys
import logging
from logging import handlers
import datetime
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Variables
past_inventory = 'past_inventory.csv'
current_inventory = 'current_inventory.csv'
aws_region = 'us-west-2'
useProxy = False
proxyIP = ''
env = 'Test'
email_distro_list = 'me@email.com'
smtp_server = 'localhost'

# Logging configuration
logger = logging.getLogger('inventory_comparison.py')
logger.setLevel(logging.DEBUG)
fileHandler = logging.handlers.SysLogHandler("/dev/log")
fileHandler.encodePriority('syslog', 'info')
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)

# Date configuration
today = date.today()
month = today.strftime("%B")
day = today.strftime("%m%d%y")

# Functions

def compare_host_lists(new_inventory, comparison_inventory):
# Will take two lists of hosts and compare them. It will create a python
# dictionary with the changed host and how it changed, either Added or Removed
    inventory_change = {}
    for host in new_inventory:
        if host[id] not in enumerate(d['id'] for d in comparison_inventory):
            inventory_change.update({host:'Added'})

    for host in comparison_inventory:
        if host[id] not in enumerate(d['id'] for d in new_inventory):
            inventory_change.update({host:'Removed'})

    return inventory_change

def ingest_inventory(inv_file):
# Converts a csv file a host object
    hosts = []
    try:
        with open(inv_file,'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                hosts.append({'id': row[0], 'ip': row[1], 'name': row[2], 'launchtime': row[3], 'state':row[4]})
    except Exception as e:
        logger.error("Error while attempting to read approved inventory list. Error is: {0}".format(e))
        print "Error reading inventory list. See /var/log/messages for more detail"
        sys.exit()
    return hosts

def print_results(changes):
# Will print the results of the comparison to the screen
    print("Inventory Changes for {0}").format(env)
    print("\n")
    for host,change_type in changes.iteritems():
        print('{0} | {1}').format(host, change_type)
    print("\n")

def email_results(email_message_body):
    # Email sender and receipient info
    sender = "inventory_changes@{0}.ns2.priv".format(env)
    recipient = email_distro_list

    # Email Message body
    contents = "Hi!\nHow are you?\nHere is the link you wanted:\nhttps://www.python.org"

    msg = MIMEText(contents
    msg['Subject'] = "AWS Inventory Change Report for {0} - {1}".format(env, day)
    msg['From'] = sender
    msg['To'] = recipient

    # Send the message via defined SMTP server.
    s = smtplib.SMTP(smtp_server)
    # use sendmail function to send message
    s.sendmail(sender, recipient, msg.as_string())
    s.quit()

def get_current_inventory():
    try:
        ec2conn = boto.ec2.connect_to_region(aws_region)
    except Exception as e:
        logger.error("Error while connecting to Ec2 to obtain inventory. Error is: {0}".format(e))
        print "Error connecting to EC2 to obtain inventory. See /var/log/messags for more detail"
        sys.exit()

    with open(current_inventory, 'w') as f:
        f.write(",".join("instance","ip","name","launchtime","state"))
        reservations = ec2conn.get_all_reservations(filters={'instance-state-name': ['pending','running','shutting-down','stopping','stopped']})
        for reservation in reservations:
            for instance in reservation.instances:
                if 'Name' in instance.tags:
                    name = instance.tags['Name']
                else:
                    name = 'No associated name tag'
                f.write(",".join(instance.id, instance.private_ip_address, name, instance.launch_time, instance.status_code))

# Main
if __name__ == "__main__":

    # Set Environment Proxy Values
    if useProxy == ' True':
        os.environ['http_proxy'] = "http://" + proxyIP + ":80"
        os.environ['https_proxy']="https://" + proxyIP + ":80"
        os.environ["NO_PROXY"] = "169.254.269.254"      # No proxy to AWS instance metadata

    # Pull current inventory and write to file identified in current_inventory variable
    get_current_inventory()

    # Convert file inventories to dictionaries for python processing
    old_hosts = ingest_inventory(past_inventory)
    new_hosts = ingest_inventory(current_inventory)

    inventory_changes = compare_host_lists(new_hosts, previous_hosts)
    print_results(inventory_changes)
    email_results(inventory_changes)
