#!/usr/bin/env python
########################################################################
#
# Update_DNS.py
#
# Boto3 script to update Route53 records
########################################################################

import json
import sys
import argparse
import boto3

# Global Variables
default_TTL = 3600

# Parse command line inputs
parser = argparse.ArgumentParser()
parser.add_argument('-d', dest='domain', help='domain')
parser.add_argument('-r', dest='host_name', help='hostname of record to create')
parser.add_argument('-t', dest='target', help='target for new DNS record')
parser.add_argument('-a', dest='action', help='Action to take for DNS, must be Add or Delete')
parser.add_argument('-z', dest='zone_id', help='Route 53 Hosted Zone ID')
inputs = parser.parse_args()

def update_route53(zone, dns_action):
    global default_TTL
    global inputs

    client = boto3.client('route53')
    try:
        response = client.change_resource_record_sets(
        HostedZoneId= zone,
        ChangeBatch= {
                'Comment': 'add %s -> %s' % (inputs.host_name, inputs.target),
                'Changes': [
                        {
                            'Action': dns_action,
                                'ResourceRecordSet': {
                                'Name': inputs.host_name + "." + inputs.domain,
                            'Type': 'CNAME',
                                'TTL': default_TTL,
                                'ResourceRecords': [{'Value': inputs.target}]
                        }
                }]
        })
    except Exception as e:
        print("Error creating Route 53 record: {0}").format(e)
        sys.exit()
    print("Success: " + inputs.host_name + ".preprodopisnet.io")


# Main Program Logic
if __name__ == '__main__':

    if inputs.action.lower() == "add":
        action = "UPSERT"
    elif inputs.action.lower() == "delete":
        action = "DELETE"
    else:
        print("Invalid DNS action passed as command -a, must be add or delete")

    update_route53(inputs.zone_id, action)
