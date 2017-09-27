import requests,json
import re

from netmiko import ConnectHandler
from netmiko.ssh_exception import *

## Disable invalid certificate warnings for APIC ##
requests.packages.urllib3.disable_warnings()


### UPDATE THESE VARIABLES FOR EACH CUSTOMER ###
APICEM_IP = "172.20.10.20"
APICUSER = 'admin'
APICPASS = '!Cnet2017!'

USERNAME = 'admin'                              # NETWORK DEVICE USERNAME
PASSWORD = '!Cnet2017!'                         # NETWORK DEVICE PASSWORD
SEARCHTAG = 'HQ'                                # SEARCH BASED ON THIS DEVICE TAG, IF EMPTY ('') THEN SEARCH ALL DEVICES
COMMANDS = ['show version', 'show ip route']    # COMMAND(S) TO RUN
###                                          ###

## AUTH WITH APIC-EM ##
def createserviceticket():
    response = requests.post(
        url="https://"+APICEM_IP+"/api/v1/ticket",
        headers={
            "Content-Type": "application/json",
        },
        verify=False,
        data=json.dumps({
            "username": APICUSER,
            "password": APICPASS
        })
    )
    output = ('Response HTTP Response Body: {content}'.format(content=response.content))
    match_service_ticket = re.search('serviceTicket":"(.*cas)', output, flags=0)
    service_ticket = match_service_ticket.group(1)
    return service_ticket

def newAPICallGET(url):
    url = "https://"+APICEM_IP+"/api/v1/"+url
    response = requests.get(url,headers={"X-Auth-Token": createserviceticket(),"Content-Type": "application/json",},verify=False)
    return response.json()

def run_commands(my_list):
    for device in my_list:
        ## Open output file ##
        with open(device['hostname'] + '.txt', 'w') as fout:

            connect_dict = {'device_type': 'cisco_ios', 'ip': device['ip'], 'username': USERNAME,
                            'password': PASSWORD}

            try:
                net_connect = ConnectHandler(**connect_dict)
            except NetMikoTimeoutException:
                error = "Unable to connect to host {} ({}) (timeout)!".format(device['hostname'],device['ip]'])
                print(error)
                fout.write(error)
                continue
            except NetMikoAuthenticationException:
                error = "Unable to connect to host {} ({}) (authentication failure)!".format(device['hostname'],device['ip'])
                print(error)
                fout.write(error)
                continue

            for command in COMMANDS:
                fout.write('\n\nRunning Command:\n'+command+'\n\n')
                output = net_connect.send_command(command)
                fout.write(output)
        fout.close()

## GRAB ALL DEVICES WITH TAG ##
def grabdevicestag(my_list):
    ip_list = []

    ## CREATE LIST OF IP ADDRESSES/HOSTNAMES TO CONNECT TO ##
    for device in my_list:
        data = newAPICallGET('network-device/{}'.format(device['resourceId']))
        temp_device = {'ip': data['response']['managementIpAddress'], 'hostname': data['response']['hostname']}
        ip_list.append(temp_device)

    run_commands(ip_list)

## GRAB ALL DEVICES ##
def graballdevices(my_list):

    ip_list = []
    for device in my_list:
        temp_device = {'ip':device['managementIpAddress'],'hostname':device['hostname']}
        ip_list.append(temp_device)

    run_commands(ip_list)

## MAIN ##

if SEARCHTAG == '':             # GRAB ALL DEVICES
    data = newAPICallGET('network-device')
    device_list = data['response']
    graballdevices(device_list)
else:                           # USE SEARCH TAG
    data = newAPICallGET('tag/association?resourceType=network-device&tag={}'.format(SEARCHTAG))
    tag_device_list = data['response']
    grabdevicestag(tag_device_list)
