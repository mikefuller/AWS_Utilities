#!/usr/bin/env python
######################################################################
# vol_backup_script.py
############################# DESCRIPTION ##############################
#
# This script will query AWS for a list of all EBS volumes with a tag with a
# key of BackupDrive and a value of Yes. Once that is found it will create a
# a snapshot of the volume and apply mandatory tags (data, source, etc)
#
# If the copy_to_alternate_region variable is set to True then it will also
# copy that snapshot to the defined alternate region within the same account
# if it is tagged with a key of ShareWithAlt and value of Yes
#
# -----------------------------------------------------------------------
# Deps. : Python 2.7+
#
########################################################################

import os
import time
from datetime import timedelta, datetime, date
import boto3

# User defined variables
region = 'us-east-1'       # define primary region to copy volumes from
copy_to_alternate_region = True
alternate_region = 'us-west-2'     # define alternate region to copy volumes too
share_to_alt_account = True
alt_account_id = 'XXXXXXXX'   #Enter the AWS Account ID for the alternate account to copy to.

# Set current month and day and time
today = date.today()
month = today.strftime("%B")
day = today.strftime("%m%d%y")
now = time.time()
time = datetime.fromtimestamp(now)
current_time = time.strftime('%H:%M:%S')


def initiate_boto_connection(region):
    ec2obj = boto3.resource('ec2', region_name=region)
    return ec2obj


def scan_for_backup_drives(ec2obj):
    backup_drives = {}
    shared_alt_drives = {}

    instances = ec2obj.instances.all()
    for instance in instances:
        if instance.tags:
            for host_tags in instance.tags:
                if host_tags['Key'] == 'Name':
                    hostname = host_tags['Value']
            for volume in instance.volumes.all():
                volID = volume.id
                if volume.tags:
                    for vol_tag in volume.tags:
                        if vol_tag['Key'] == 'BackupDrive':
                            vol_tag_value = vol_tag['Value']
                            if vol_tag_value.lower() == 'yes':
                                backup_drives.update({volID: hostname})
                        if vol_tag ['Key'] == 'ShareWithAlt':
                            vol_tag_value = vol_tag['Value']
                            if vol_tag_value.lower() == 'yes':
                                shared_alt_drives.update({volID: hostname})
    return backup_drives, shared_alt_drives


def create_snapshot(ec2obj, vol_id, hostname):
    snapshot = ec2obj.create_snapshot(VolumeId=vol_id, Description='Volume backup for {0} - {1}'.format(hostname, vol_id))
    update_snapshot_tag(ec2obj, snapshot, hostname)
    return snapshot.id


def update_snapshot_tag(ec2obj, snapshot, hostname):
    global day
    global now
    snapshot_tag = [
        {
            'Key': 'Date_Created',
            'Value': day
        },
        {
            'Key': 'Time_Created',
            'Value': current_time
        },
        {
            'Key': 'Source Server',
            'Value': hostname
        }
    ]

    tag = snapshot.create_tags(Tags=snapshot_tag)
    return tag


def copy_to_second_region(snapshot_id, hostname):
    client = boto3.client('ec2', alternate_region)
    response = client.copy_snapshot(
        SourceSnapshotId=snapshot_id,
        DestinationRegion=alternate_region,
        SourceRegion=region,
        Description="Backup Volume Snapshot from Primary Region"
    )

def share_snapshot_to_alt(ec2obj, snapshot_id):
    snapshot = ec2obj.Snapshot(snapshot_id)
    snapshot.modify_attribute(
        Attribute='createVolumePermission',
        CreateVolumePermission={
            'Add': [
                {
                 'UserId': alt_account_id
                }
            ]
        }
    )

def lambda_handler(event, context):
    snapshots_created = {}
    ec2obj = initiate_boto_connection(region)

    # Scan EBS volumes for backupdrive tag
    backupdrives, sharedaltdrives = scan_for_backup_drives(ec2obj)

    # Create snapshot and tag each drive in backupdrives dictionary. Then create a dictionary of all snapshots created
    for key, value in backupdrives.iteritems():
        volID = key
        hostname = value
        snapshot_id = create_snapshot(ec2obj, volID, hostname)
        if copy_to_alternate_region is True:
            copy_to_second_region(snapshot_id, hostname)
        snapshots_created.update({volID: snapshot_id})

    # Share backups with with alternate AWS account (if volume was tagged with ShareWithAlt)
    if share_to_alt_account  is True:
        for key, value in sharedaltdrives.iteritems():
            for vol_id, snap_id in snapshots_created.iteritems():
                if key is vol_id:
                    share_snapshot_to_alt(ec2obj, snap_id)