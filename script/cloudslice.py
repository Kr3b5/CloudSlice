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




#-------------------------------------------------------------------------------
#                                   CONFIG
#-------------------------------------------------------------------------------


ec2 = boto3.resource('ec2')

instance_id = ['i-0dc8a2dbfad73a683']

cUser       = 'ubuntu'
cKey        = './key/Key_1.pem'

u_lPath   = './test/cube.stl'
d_lPath   = './test/cube.gcode'

u_rPath  = '/home/ubuntu/temp.stl'
d_rPath  = '/home/ubuntu/temp.gcode'

#-------------------------------------------------------------------------------
#                                   MAIN
#-------------------------------------------------------------------------------

def main():
    header()

    print( 'Number of arguments:', len(sys.argv), 'arguments.' )
    print( 'Argument List:', str(sys.argv) )

    # First State Check
    if( getinstancesstate() == 80 ):
        printcmd("Start instance...")
        startinstance()
    elif(getinstancesstate() == 16):
        printcmd("Instance already running...")
    else:
        printcmd("Wait for instance...")
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
            printcmd("Wait for SSH server...")
            sleep(20)
            break

    # Get instance DNS
    server = getinstancesDNS()
    printcmd(server)

    if( getinstancesstate() == 16 ):
        # SCP upload:
        printcmd("Upload file...")
        putSCP(server , u_lPath, u_rPath)
        printcmd("File upload complete!")

        # SSH command:
        command = 'slic3r temp.stl --output temp.gcode'
        printcmd("Start slice process...")
        makeSSH(server, command)
        printcmd("Slice process complete!")

        # SCP download:
        printcmd("Download GCODE...")
        getSCP(server, d_lPath, d_rPath)
        printcmd("GCODE download complete! File Path: " + d_lPath)

        # Stop instance
        printcmd("Stop instance...")
        stopinstance()
    else:
        printcmd("Error! Instance is stopped!")


#-------------------------------------------------------------------------------
#                                   FUNCTIONS
#-------------------------------------------------------------------------------

#==================================AWS==================================

def startinstance():
    try:
        response = ec2.instances.filter(InstanceIds=instance_id).start()
        #printcmd(response)
    except ClientError as e:
        printcmd(e)

def stopinstance():
    try:
        response = ec2.instances.filter(InstanceIds=instance_id).stop()
        #printcmd(response)
    except ClientError as e:
        printcmd(e)

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
    printcmd(str(lines))
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

def printcmd(s):
    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("[%b %d %y %H:%M:%S]")
    print(f"{timestampStr} {s}" )



#-------------------------------------------------------------------------------
#                              START
#-------------------------------------------------------------------------------



if __name__ == '__main__':
   main()
