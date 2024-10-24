# ssh-connect.py #

## Description ##
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

## Note: ##
This script requires the AWS CLI to be installed and configured with the
appropriate permissions.

It includes functions for AWS SSO login, setting AWS environment variables,
starting EC2 instances, and initiating SSM sessions.

## Author ##
James D. Flatten
<davin.flatten@asciionly.com>
