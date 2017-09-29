#!/usr/bin/env python
########################################################################
#
# SecurityGroupCleanup.py
#
############################# DESCRIPTION ##############################
#
# This script will query all security groups in the environment and identify
# security groups that are unassociated with any EC2 instances. It will run in
# one of two modes. List mode will display all Security Groups that are
# not applied to any host but not take any action on them. Delete mode will
# delete hosts in one of 3 modes. The user will pass the delete flag an option.
# specifically, 'manual, 'single', or 'all'. The manual mode will step through
# every unassociated security group one by one and ask the user if they would like
# to delete the group or skip it. The single option will allow the user to pass
# in a specific security group ID and have only that group deleted. The all option
# will perform a batch delete of all unassociated security groups.
#
# to run in list mode enter SecurityGroupCleanup.py --list
# to run in delete mode enter SecurityGroupCleanup.py --delete <option>
#
# option must be one of the following. If no option is passed the script will exit
#       manual          (i.e. python SecurityGroupCleanup,py --delete manual)
#       single <sg ID>  (i.e. python SecurityGroupCleanup,py --delete single sg-1237564)
#       all             (i.e. python SecurityGroupCleanup,py --delete all)
#
# Note that within this script the user should make sure the region variable is
# accurate and if a proxy is in use then use_proxy should be changed to True and
# the proxyIP variable should be set to the IP of the proxy. The script assumes
# the proxy runs on port 80.
#-----------------------------------------------------------------------
# Deps. : Python 2.6+, boto 2.0
# The instance that the script is executing on must have an IAM role granting it
# permission to query EC2 and delete security groups in EC2
########################################################################

# import statements
import boto
from boto import ec2
import sys

# Variables
region = "us-east-1"
use_proxy = "False"
proxyIP = "0.0.0.0"
mode = sys.argv[1]
valid_options = ['--list', '--delete']

if use_proxy == 'True':
    os.environ['http_proxy'] = "http://" + proxyIP + ":80"
    os.environ['https_proxy']="https://" + proxyIP + ":80"
    os.environ["NO_PROXY"] = "169.254.269.254"      # No proxy to AWS instance metadata

if mode not in valid_options:
    print "Unrecognized flag. Please append --list or --delete <option>"
    print " Delete options are: "
    print "    single <security group id>     - This will delete the single security group ID passed"
    print "    all                            - This will delete all unassociated security groups as a batch"
    print "    manual                         - This will walk through each unassociated security group ad allow user to delete or keep each one"
    sys.exit()

# Connect to EC2
ec2conn = boto.ec2.connect_to_region(region)

# Execute commands against security groups based on flag passed by user

if mode == '--list':
    # Run program in list mode. All unassociated Security Groups will be displayed on screen but not deleted
    # Get list of unused Security groups
    unused_security_groups = ec2conn.get_all_security_groups(filters = {'vpc-id' : '*'})
    print "The following Security groups are currently not associated with any EC2 instance:"
    for i in unused_security_groups:
        if len(i.instances()) == 0:
            print ("- {0} | {1}").format(i.name, i.id)
    sys.exit()

if mode =='--delete':
    if len(sys.argv) >=3:    #check to see if an option was passed along with the delete flag
        option = sys.argv[2]
    else:
        print "The delete flag was passed without an option (i.e --delete <option>). Please pass an option (single <sg id>, manual, all"
        sys.exit()
    if option == 'single':
        # Delete individual security group that is passed in by user
        sg = str(sys.argv[3])
        print "Test this is the sg {0}".format(sg)
        print("This action will delete security group {0}. Press y to continue or any other key to cancel").format(sg)
        confirm = (raw_input(">> ")).lower()
        if confirm == 'y':
            ec2conn.delete_security_group(group_id = sg))
            print("Security group {0} deleted").format(sg)
            sys.exit()
        else:
            print "Deletion cancelled"
            sys.exit()

    if option =='manual':
        # Run program in manual delete mode. User will be prompted per Security Group to delete
        unused_security_groups = ec2conn.get_all_security_groups(filters = {'vpc-id' : '*'})
        for i in unused_security_groups:
            print("Delete Security Group '{0}' | {1} ?. Press y to continue or any other key skip this group to proceed to the next one").format(i.name, i.id)
            selection = (raw_input(">> "))
            selection = selection.lower()
            if selection == 'y':
                print("Confirm Security group '{0}' is to be deleted. Press y to confirm or any other key to cancel").format(i.name)
                confirm = (raw_input(">> ")).lower()
                if confirm == 'y':
                    ec2conn.delete_security_group(group_id = i.id)
                    print("Security group {0} | {1} deleted").format(i.name,i.id)
                else:
                    print "Deletion cancelled"
            else:
                print("Security Group {0} has not been deleted").format(i.name)
        sys.exit()

    if option =='all':
        # This mode will delete all unassociated security groups as a batch job. The user will be asked to confirm
        # before the action is taken
        print "This action will delete all security groups that are not associated with any EC2 instance. This is not reversible"
        print "To continue press y. To cancel press any other key."
        confirm = (raw_input(">> ")).lower()
        if confirm == 'y':
            unused_security_groups = ec2conn.get_all_security_groups(filters = {'vpc-id' : '*'})
            for i in unused_security_groups:
                ec2conn.delete_security_group(group_id = i.id)
                print("Security group {0} | {1} deleted").format(i.name,i.id)
        else:
            print "Deletion cancelled"
            sys.exit()
