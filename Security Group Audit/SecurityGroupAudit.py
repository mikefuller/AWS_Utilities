#!/usr/bin/env python
########################################################################
#
# Script will generate an inventory list of all instances in EC2 and also a
# list of all instances with the a user provided Security Group applied. A diff will
# then be conducted to identify hosts in the overall inventory that don't have
# the requested security group applied
#
# When calling the user should pass the following:
#      -s <SecurityGroup Name to audit against>
#      -r <AWS region to audit against>
#
#-----------------------------------------------------------------------
# Deps. : Python 2.6+, boto 2.0
########################################################################

import boto
from boto import ec2
import os
import argparse

#Set proxy
os.environ['http_proxy'] = "http://10.4.249.101:80"
os.environ['https_proxy'] = "http://10.4.249.101:80"
os.environ['NO_PROXY'] = "169.254.169.254"

# Obtain user values
parser = argparse.ArgumentParser()
parser.add_argument('-s', dest='securitygroup', help='security group to audit on')
parser.add_argument('-r', dest='region', help='aws region to query')
inputs = parser.parse_args()
sg = inputs.securitygroup
region = inputs.region

allInstances =[]
sgAppliedInstances =[]

ec2conn = boto.ec2.connect_to_region(region)
fullReservations = ec2conn.get_all_instances()
fullInstances = [i for r in fullReservations for i in r.instances]
for i in fullInstances:
    allInstances.append(i.id)

appliedReservations = ec2conn.get_all_instances(filters={'instance.group-name': sg})
appliedInstances = [i for r in appliedReservations for i in r.instances]
for i in appliedInstances:
    sgAppliedInstances.append(i.id)

print "Hosts with Security Group: {0} not applied:".format(sg)
for host in allInstances:
    if host not in sgAppliedInstances:
        print host