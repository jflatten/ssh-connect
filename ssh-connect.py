#!/usr/bin/env python3

"""
This script can be used from inside a OpenSSH client config file to utlize the ssh
command to start an stopped EC2 and then connect to the instance using SSM instead 
of the native ssh protocol.  The script depends on the environment utilzing AWS
SSO login and the AWS CLI.

Add the following to your config file:
    
    Host myhost
      User ec2-user
      Port 22
      ProxyCommand /usr/bin/python3 ssh-connect.py --target i-0c3f97820e0c423ie --port %p

This script will attempt to log in to AWS SSO using the default profile.  If the
login is successful, it will set the AWS_PROFILE and AWS_DEFAULT_REGION
environment variables based on the provided host and port.  It will then start the
EC2 instance and wait for the instance to be fully operational.  Once the instance 
is ready, it will initiate an SSM session and connect to the instance using SSM.

Note:
    This script requires the AWS CLI to be installed and configured with the
    appropriate permissions.

It includes functions for AWS SSO login, setting AWS environment variables,
starting EC2 instances, and initiating SSM sessions.
"""

import os
import platform
import sys
import argparse
import boto3
import subprocess
from botocore.exceptions import ClientError

def loggedin() -> bool:
    """
    Check if the user is logged in to AWS SSO.

    Returns:
        bool: True if logged in, False otherwise.
    """
    try:
        sts = boto3.client('sts')
        sts.get_caller_identity()
        print("Logged in to AWS SSO")
        return True
    except:
        print("Not logged in to AWS SSO")
        return False

def login():
    """
    Attempt to log in to AWS SSO using the default profile.

    Raises:
        Exception: If the login process fails.
    """
    try:
        os.system('aws sso login --profile default')
    except Exception as e:
        raise e

def set_aws_environment(profile, region):
    """
    Set AWS_PROFILE and AWS_DEFAULT_REGION environment variables.

    Args:
        profile (str): The AWS profile name to set.
        region (str): The AWS region to set.

    Note:
        On Windows, this function uses 'setx' and requires restarting the command prompt.
        On Linux/macOS, it sets variables for the current session only.
    """
    system = platform.system().lower()

    if system == 'windows':
        os.system(f'setx AWS_PROFILE {profile}')
        os.system(f'setx AWS_DEFAULT_REGION {region}')
        print("Environment variables set. Please restart your command prompt for changes to take effect.")
    elif system in ['linux', 'darwin']:
        os.environ['AWS_PROFILE'] = profile
        os.environ['AWS_DEFAULT_REGION'] = region
        print("Environment variables set for the current session.")
    else:
        print(f"Unsupported operating system: {system}")
        return

def start_instance(instance_id) -> bool:
    """
    Start an EC2 instance and wait for it to be fully operational.

    Args:
        instance_id (str): The ID of the EC2 instance to start.

    Returns:
        bool: True if the instance started successfully, False otherwise.
    """
    ec2 = boto3.client('ec2')
    
    try:
        ec2.start_instances(InstanceIds=[instance_id])
        print(f"Starting EC2 instance {instance_id}")
        
        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        print(f"EC2 instance {instance_id} is now running")
        
        waiter = ec2.get_waiter('instance_status_ok')
        waiter.wait(InstanceIds=[instance_id])
        print(f"EC2 instance {instance_id} is now online and ready")
        
        return True
    except ClientError as e:
        print(f"Error starting EC2 instance {instance_id}: {e}")
        return False

def main(arguments):
    """
    Main function to parse arguments and execute the primary script logic.

    Args:
        arguments (list): Command line arguments.

    Returns:
        int: Exit code of the script.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-t','--target', help="Target system to connect to with SSM")
    parser.add_argument('-p','--port', help="Port for the SSH connection. Default: 22")
    parser.add_argument('-r', '--region', help="AWS region to connect to. Default: us-east-1")
    parser.add_argument('--profile', help="AWS profile to use. Default: default")
    parser.set_defaults(region='us-east-1', profile='default', port=22)
    args = parser.parse_args(arguments)

    set_aws_environment(args.profile, args.region)

    if not loggedin():
        login()

    start_instance(args.target)

    ssm_command = ["aws", "ssm", "start-session", "--target", args.target, "--document-name", "AWS-StartSSHSession", "--parameters", "portNumber=" + args.port]

    try:
        subprocess.run(ssm_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
