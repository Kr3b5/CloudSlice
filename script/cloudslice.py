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
localpath   = './Baby_Yoda_v2.2.stl'
remotepath  = '/home/ubuntu/yoda.stl'

#-------------------------------------------------------------------------------
#                                   MAIN
#-------------------------------------------------------------------------------

def main():
    header()

    print( 'Number of arguments:', len(sys.argv), 'arguments.' )
    print( 'Argument List:', str(sys.argv) )

    #printcmd( getinstancesstate() )

    #sleep(2)

    #startinstance()

    #sleep(15)

    printcmd( getinstancesstate() )
    startSSH( getinstancesDNS() )

    sleep(5)

    stopinstance()

    sleep(2)

    printcmd( getinstancesstate() )
#-------------------------------------------------------------------------------
#                                   FUNCTIONS
#-------------------------------------------------------------------------------

def startinstance():
    try:
        response = ec2.instances.filter(InstanceIds=instance_id).start()
        printcmd(response)
    except ClientError as e:
        printcmd(e)

def stopinstance():
    try:
        response = ec2.instances.filter(InstanceIds=instance_id).stop()
        printcmd(response)
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

def startSSH(server):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server, username=cUser, key_filename=cKey )
    sftp = ssh.open_sftp()
    sftp.put(localpath, remotepath)
    sftp.close()
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
