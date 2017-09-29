#!/usr/bin/env python
######################################################################
# Update_Uptrends.py
############################# DESCRIPTION ##############################
#
#-----------------------------------------------------------------------
#
# Usage Notes  :
#
#
########################################################################

# Module Imports
import requests
from requests.auth import HTTPBasicAuth
import json
import time
import sys
import datetime
from datetime import timedelta, datetime, date
import argparse

# Global Variables
SSL_verify = True
uptrends_url = 'https://api.uptrends.com/v3'

# Parse command line inputs
parser = argparse.ArgumentParser()
parser.add_argument('-u', dest='username', help='username for uptrends')
parser.add_argument('-p', dest='passwd', help='password for uptrends account')
parser.add_argument('-n', dest='name', help='application and service name')
parser.add_argument('-s', dest='siteurl', help='url for the site to be monitored')
parser.add_argument('-a', dest='alerts', help='true or false on whether alerts should be generated')
parser.add_argument('-m', dest='method', help='identify action to create, list, or delete monitor. Value should be create, list, or monitor')
parser.add_argument('-g', dest='guid', help='identify guid of existing monitor to delete')
inputs = parser.parse_args()

# Set current month and day
today = date.today()
month = today.strftime("%B")
day = today.strftime("%m%d%y")

#############################################
# Functions

def send_request(method, data, probeguid='000'):
    global inputs
    global uptrends_url
    postHeaders = {'Content-Type':'application/json', 'Accept':'application/json'}
    headers = {'Content-Type':'multipart/form-data', 'Accept':'application/json'}
    data = json.dumps(data)

    try:
        if method == 'POST':
            resource_url = uptrends_url + '/probes'
            r = requests.post(resource_url, auth=(inputs.username, inputs.passwd), data=data, headers=postHeaders, verify=SSL_verify)
        elif method == 'PUT':
            resource_url = uptrends_url + '/probes/' + probeguid
            r = requests.put(resource_url, auth=(inputs.username, inputs.passwd), data=data, headers=headers, verify=SSL_verify)
        elif method == 'DELETE':
            resource_url = uptrends_url + '/probes/' + probeguid
            r = requests.delete(resource_url, auth=(inputs.username, inputs.passwd), data=data, headers=headers, verify=SSL_verify)
        elif method == 'GET':
            resource_url = uptrends_url + '/probes/' + probeguid
            r = requests.get(resource_url, auth=(inputs.username, inputs.passwd), data=data, headers=headers, verify=SSL_verify)
        else:
            #assume list of all probes here (still a get call)
            resource_url = uptrends_url + '/probes'
            r = requests.get(resource_url, auth=(inputs.username, inputs.passwd), headers=headers, verify=SSL_verify)
    except Exception as e:
        print "Error connecting to Uptrends API. Error is {0}".format(e)
        sys.exit()

    if r.status_code == 200:
        return r.content
    elif r.status_code ==201:
        response = r.json()
        guid = response['Guid']
        return r.content, guid
    else:
        e = r.json()
        print("Monitor creation failed: {0}").format(e)
        return "fail"

def create_monitor():
    global inputs
    # Function will get a list of all job history IDs associated with a specific scan ID.
    # It will return the history ID and last modification date
    data = {'Name':inputs.name,
            'URL':inputs.siteurl,
            'Port':80,
            'CheckFrequency':5,
            'ProbeType':"Http",
            'IsActive':True,
            'GenerateAlert':inputs.alerts,
            'Notes':"",
            'PerformanceLimit1':2500,
            'PerformanceLimit2':5000,
            'ErrorOnLimit1':False,
            'ErrorOnLimit2':False,
            'Timeout':30000,
            'TcpConnectTimeout':10000,
            'DnsLookupMode':"Local",
            'IsCompetitor':False,
            'Checkpoints':"",
            'DNSQueryType':"CNAMERecord"
            }
    response = send_request('POST', data=data)
    return response

def list_monitors():
    data = ""
    response = send_request('LIST', data)
    return response

def get_monitor(probeguid):
    data = ""
    response = send_request('GET', data, probeguid)
    return response

def delete_monitor(probeguid):
    data = ""
    response = send_request('DELETE', data, probeguid)
    return response

# Main Program Logic
if __name__ == '__main__':

    if inputs.method.lower() == "create":
        response = create_monitor()
        if response == "fail":
            print("Monitor creation was unsuccessful")
        else:
            print("Success:{0}").format(response)
    elif inputs.method.lower() == "list":
        if inputs.guid:
            response = get_monitor(inputs.guid)
            if response == "fail":
                print("Monitor list was unsuccessful")
            else:
                print("Success:{0}").format(response)
        else:
            response = list_monitors()
            if response == "fail":
                print("Monitor list was unsuccessful")
            else:
                print("Success:{0}").format(response)
    elif inputs.method.lower() == "delete":
        response = delete_monitor(inputs.guid)
        if response == "fail":
            print("Monitor deletion was unsuccessful")
        else:
            print("Success")
    else:
        print("Invalid method (-m) value")
