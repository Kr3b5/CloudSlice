"""
##################################################
                SCRIPT INFORMATION
##################################################
## Author: Kevin Lempert, Jonas Renz
## Copyright: Copyright 2020, CloudSlice
## Version: 1.0.0

##################################################
                DEV INFORMATION
##################################################
States:
    0 : pending
    16 : running
    32 : shutting-down
    48 : terminated
    64 : stopping
    80 : stopped

scp:
    scp -i .\key\Key_1.pem file.stl ubuntu@[instancedns]:/home/ubuntu/file.stl

ssh:
    ssh -i .\key\Key_1.pem ubuntu@[instancedns]

slice:
    slic3r file.stl --output file.gcode [options]
"""

from time import sleep
from datetime import datetime
import sys
import boto3
from botocore.exceptions import ClientError
import os
import paramiko
import logging


#-------------------------------------------------------------------------------
#                                   CONFIG
#-------------------------------------------------------------------------------

# AWS instance
instance_id = ['i-0dc8a2dbfad73a683']

# Credentials
cUser       = 'ubuntu'
cKey        = './key/Key_1.pem'

# upload/download Path AWS
u_rPath  = '/home/ubuntu/temp.stl'
d_rPath  = '/home/ubuntu/temp.gcode'

# Print parameter list for wizard
# add new parameters here
# Input text wizard : cmd slic3r
cmddict = {
  "> Layer height ( 0.2 - 1 )     " : "--layer-height",
  "> Temperature ( 100-250 )      " : "--temperature",
  "> Bed temperature ( 0-100 )    " : "--bed-temperature",
  "> Cooling ( true/false )       " : "--cooling",
  "> Support ( true/false )       " : "--support-material",
  "> Fill Density ( 0-100 )       " : "--fill-density",
  "> Filament Diameter ( 1.75/3 ) " : "--filament-diameter",
  "> Nozzle Diameter ( 0.4-2 )    " : "--nozzle-diameter",
  "> Retract Length ( 0-10 )      " : "--retract-length",
  "> Scale  ( 1 = orginalsize )   " : "--scale"
}

# List for commands
cmdlist = list()

# init boto3
ec2 = boto3.resource('ec2')

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)

#-------------------------------------------------------------------------------
#                                   MAIN
#-------------------------------------------------------------------------------

# main function
def main():

    header()

    startwizard()

    stime_ssh = 20

    # First State Check
    if( getinstancesstate() == 80 ):
        logging.info("Start instance...")
        startinstance()
    elif(getinstancesstate() == 16):
        logging.info("Instance already running...")
        stime_ssh = 5
    else:
        logging.info("Wait for instance...")
        while True:
            sleep(2)
            if(getinstancesstate() == 16 or getinstancesstate() == 80):
                if(getinstancesstate() == 80):
                    startinstance()
                break

    # Wait for instance start
    while True:
        sleep(3)
        if(getinstancesstate() == 16):
            logging.info("Wait for SSH server...")
            sleep(stime_ssh)
            break

    # Get instance DNS
    server = getinstancesDNS()
    logging.info(server)

    if( getinstancesstate() == 16 ):
        # SCP upload:
        logging.info("Upload file...")
        putSCP(server , u_lPath, u_rPath)
        logging.info("File upload complete!")

        # SSH command:
        command = buildcommand()
        logging.info("Start slice process...")
        makeSSH(server, command)
        logging.info("Slice process complete!")

        # SCP download:
        logging.info("Download GCODE...")
        getSCP(server, d_lPath, d_rPath)
        logging.info("GCODE download complete! File Path: " + d_lPath)

        # Stop instance
        logging.info("Stop instance...")
        stopinstance()
    else:
        logging.error("Error! Instance is stopped!")

#-------------------------------------------------------------------------------
#                                   WIZARD
#-------------------------------------------------------------------------------

# wizard for print parameters
def startwizard():

    global u_lPath
    global d_lPath

    logging.info("Starting WIZARD!")
    print(">>> File parameters (false=default)")

    while(True):
        u_lPath   = input("   Path input file (path/filename.stl): ")
        if( os.path.isfile(u_lPath) ):
            break
        else:
            logging.error("File " + u_lPath + " doesnt exist!")

    d_lPath = input("   Path output file (path/filename.gcode): ")

    print("\n>>> Print parameters")
    for key, item in cmddict.items():
        value = input("   " + key + ": ")
        if(value.lower() in "true"):
            cmdlist.append( item )
        elif(value.lower() not in "false"):
            cmdlist.append( item + " " + value )

    print()

# build slic3r command
def buildcommand():
    command = 'slic3r ' + u_rPath + ' --output ' + d_rPath
    for value in cmdlist:
        command = command + " " + value
    return command

#-------------------------------------------------------------------------------
#                                   FUNCTIONS
#-------------------------------------------------------------------------------

#==================================AWS==================================

# start instance
def startinstance():
    try:
        response = ec2.instances.filter(InstanceIds=instance_id).start()
    except ClientError as e:
        logging.error(e)

# stop instance
def stopinstance():
    try:
        response = ec2.instances.filter(InstanceIds=instance_id).stop()
    except ClientError as e:
        logging.error(e)

# get instance state
def getinstancesstate():
    instances = ec2.instances.filter(InstanceIds=instance_id)
    for instance in instances:
        return(instance.state.get("Code"))

# get DNS from instance
def getinstancesDNS():
    instances = ec2.instances.filter(InstanceIds=instance_id)
    for instance in instances:
        return(instance.public_dns_name)


#==================================SCP==================================

# SCP - upload
def putSCP(server, lPath, rPath):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server, username=cUser, key_filename=cKey )
    sftp = ssh.open_sftp()
    sftp.put(lPath, rPath)
    sftp.close()
    ssh.close()

# SCP - download
def getSCP(server, lPath, rPath):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server, username=cUser, key_filename=cKey )
    sftp = ssh.open_sftp()
    sftp.get(rPath,lPath)
    sftp.close()
    ssh.close()

#==================================SSH==================================

# start SSH connection
def makeSSH(server, command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server, username=cUser, key_filename=cKey )
    stdin, stdout, stderr = ssh.exec_command(command)
    lines = stdout.readlines()
    logging.debug(str(lines))
    ssh.close()


#-------------------------------------------------------------------------------
#                              PRINT-INFOS
#-------------------------------------------------------------------------------

# Print CMD header
def header():

        print("  _____ _                 _  _____ _ _           ")
        print(" / ____| |               | |/ ____| (_)          ")
        print("| |    | | ___  _   _  __| | (___ | |_  ___ ___  ")
        print("| |    | |/ _ \| | | |/ _` |\___ \| | |/ __/ _ \ ")
        print("| |____| | (_) | |_| | (_| |____) | | | (_|  __/ ")
        print(" \_____|_|\___/ \__,_|\__,_|_____/|_|_|\___\___| ")
        print("             Created by Jonas R. & Kevin L.      ")
        print("")

#-------------------------------------------------------------------------------
#                              START
#-------------------------------------------------------------------------------

# start point
if __name__ == '__main__':
   main()
