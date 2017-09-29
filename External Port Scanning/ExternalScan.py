#!/usr/bin/env python
############################# DESCRIPTION ##############################
#
# This script will take a target list and approved ports list as input. It
# will then run a port scan against each host in the target list and compare
# that to the approved ports. If there are differences it will write that
# to the screen.
#
#-----------------------------------------------------------------------
# Deps. : Python 2.7+
#
# Usage Notes  :
#
#               i.e.  python ExternalScan.py <target file> <mode>
#
#               target file is just a csv file. See the Approved_ports_List.csv sample file
#
#       mode can be:
#           --details
#           --audit
#
#       if no options are selected then it defaults to audit mode
#
########################################################################

import sys
import logging
from logging import handlers
import os
import socket
import nmap
import csv

nmap_scan_options = '-sT'

# Logging configuration
#logger = logging.getLogger("External Exposure Scan")
#logger.setLevel(logging.DEBUG)
#fileHandler = logging.handlers.SysLogHandler("/dev/log")
#fileHandler.encodePriority('syslog', 'info')
#formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
#fileHandler.setFormatter(formatter)
#logger.addHandler(fileHandler)


# Functions

def analyze_discovered_ports(nscanner,approved_ports,mode):
    for host in nscanner.all_hosts():
        open_ports = []
        if mode == '--details':
            print('----------------------------------------------------')
            print('Host : %s (%s)' % (host, nscanner[host].hostname()))
            print('State : %s' % nscanner[host].state())
            for proto in nscanner[host].all_protocols():
                print('----------')
                print('Protocol : %s' % proto)
                lport = nscanner[host][proto].keys()
                lport.sort()
                for port in lport:
                    print ('port : %s\tstate : %s' % (port, nscanner[host][proto][port]['state']))
        if mode == '--audit':
            if nscanner[host].state() == 'up':
                for proto in nscanner[host].all_protocols():
                    lport = nscanner[host][proto].keys()
                    for port in lport:
                        if nscanner[host][proto][port]['state'] == 'open':
                            open_ports.append(str(port))
                compare_to_authorized(host, open_ports, approved_ports)
            else:
                print("Host not reachable: {0}").format(host)

def compare_to_authorized(target, found_ports, approved_ports):
    target_approved_ports = approved_ports[target].split()

    for i in found_ports:
        if i not in target_approved_ports:
            print("Unauthorized Port Identified. Host: {0}, Port: {1}").format(target,i)

def execute_port_scan(targets):
    nscanner = nmap.PortScanner()
    print "Running port scans ..."
    nscanner.scan(hosts=targets,arguments=nmap_scan_options)
    return nscanner

def get_targets(target_file):
        try:
            targets_list = [line.rstrip() for line in open(target_file)]
            targets = ' '.join(targets_list)
        except Exception as e:
#            logger.error("Error while attempting to read target list. Error is: {0}".format(e))
            print "Error reading target list. See /var/log/messages for more detail"
            sys.exit()
        return targets

def get_approved_ports(approved_ports_file):
    approved_ports_dict = {}
    try:
        with open(approved_ports_file) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                approved_ports_dict.update({row['Host']:row['AllowedPorts']})
            return approved_ports_dict
    except Exception as e:
#        logger.error("Error while attempting to read approved ports list. Error is: {0}".format(e))
        print e
        print "Error reading approved ports list. See /var/log/messages for more detail"
        sys.exit()

# Main
if __name__ == "__main__":

    # Collect and validate user input
    mode_flag = ''
    approved_modes = ('--details', '--audit')
    target_file = sys.argv[1]
    approved_ports_file = sys.argv[2]
    if len(sys.argv) >=4:    #check to see if an option was passed along with the target host if not default to audit
        mode_flag = sys.argv[3]
        if mode_flag not in approved_modes:
            print("improper mode flag passed, only use --audit or --details or do not pass a mode flag")
            sys.exit()
    else:
        mode_flag = '--audit'

    # run scripts to gather targets and approved hosts and run nmap scanner
    approved_ports = get_approved_ports(approved_ports_file)
    targets = get_targets(target_file)
    scan_results = execute_port_scan(targets)
    analyze_discovered_ports(scan_results,approved_ports, mode_flag)
