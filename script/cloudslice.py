"""
States:
    0 : pending
    16 : running
    32 : shutting-down
    48 : terminated
    64 : stopping
    80 : stopped

scp:
    scp -i .\key\Key_1.pem Baby_Yoda_v2.2.stl ubuntu@ec2-54-146-91-178.compute-1.amazonaws.com:/home/ubuntu/yoda.stl

ssh:
    ssh -i .\key\Key_1.pem ubuntu@ec2-54-146-91-178.compute-1.amazonaws.com

slice:
    slic3r cube.stl --output cube.gcode

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

ec2 = boto3.resource('ec2')

instance_id = ['i-0dc8a2dbfad73a683']

cUser       = 'ubuntu'
cKey        = './key/Key_1.pem'

u_lPath   = ''
d_lPath   = ''

u_rPath  = '/home/ubuntu/temp.stl'
d_rPath  = '/home/ubuntu/temp.gcode'

cmddict = {
  "Layer height"    : "--layer-height",
  "Temperature"     : "--temperature",
  "Bed temperature" : "--bed-temperature",
}

cmdlist = list()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)

#-------------------------------------------------------------------------------
#                                   MAIN
#-------------------------------------------------------------------------------

def main():
    header()

    startwizard()

    # First State Check
    if( getinstancesstate() == 80 ):
        logging.info("Start instance...")
        startinstance()
    elif(getinstancesstate() == 16):
        logging.info("Instance already running...")
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
            sleep(20)
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

def startwizard():
    logging.info("Starting WIZARD!")
    print(">>> File parameters")
    u_lPath   = input("   Path input file (path/filename.stl): ")
    d_lPath   = input("   Path output file (path/filename.gcode): ")

    print("\n>>> Print parameters")
    for key, item in cmddict.items():
        value = input("   " + key + ": ")
        cmdlist.append( item + " " + value )

    print()

    # TEST TODO: remove
    command = buildcommand()
    logging.debug(command)
    exit()
    #===================================

def buildcommand():
    command = 'slic3r ' + u_rPath + ' --output ' + d_rPath
    for value in cmdlist:
        command = command + " " + value
    return command

#-------------------------------------------------------------------------------
#                                   FUNCTIONS
#-------------------------------------------------------------------------------

#==================================AWS==================================

def startinstance():
    try:
        response = ec2.instances.filter(InstanceIds=instance_id).start()
    except ClientError as e:
        logging.error(e)

def stopinstance():
    try:
        response = ec2.instances.filter(InstanceIds=instance_id).stop()
    except ClientError as e:
        logging.error(e)

def getinstancesstate():
    instances = ec2.instances.filter(InstanceIds=instance_id)
    for instance in instances:
        return(instance.state.get("Code"))

def getinstancesDNS():
    instances = ec2.instances.filter(InstanceIds=instance_id)
    for instance in instances:
        return(instance.public_dns_name)


#==================================SCP==================================

def putSCP(server, lPath, rPath):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server, username=cUser, key_filename=cKey )
    sftp = ssh.open_sftp()
    sftp.put(lPath, rPath)
    sftp.close()
    ssh.close()

def getSCP(server, lPath, rPath):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server, username=cUser, key_filename=cKey )
    sftp = ssh.open_sftp()
    sftp.get(rPath,lPath)
    sftp.close()
    ssh.close()

#==================================SSH==================================

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



if __name__ == '__main__':
   main()
