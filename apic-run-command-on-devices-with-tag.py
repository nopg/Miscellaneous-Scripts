import requests,json
import re

from netmiko import ConnectHandler
from netmiko.ssh_exception import *

### Disable invalid certificate warnings.
requests.packages.urllib3.disable_warnings()

apicem_ip = "172.20.10.20"

def createserviceticket():
    response = requests.post(
        url="https://"+apicem_ip+"/api/v1/ticket",
        headers={
            "Content-Type": "application/json",
        },
        verify=False,
        data=json.dumps({
            "username": 'admin',        ## APIC-EM USERNAME
            "password": '!Cnet2017!'    ## APIC-EM PASSWORD
        })
    )
    output = ('Response HTTP Response Body: {content}'.format(content=response.content))
    match_service_ticket = re.search('serviceTicket":"(.*cas)', output, flags=0)
    service_ticket = match_service_ticket.group(1)
    return service_ticket

## LOGIN INFORMATION FOR NETWORK DEVICES ##
USERNAME = 'admin'
PASSWORD = '!Cnet2017!'

## SEARCH FOR DEVICES BASED ON TAG ##
SEARCHTAG = 'HQ'

## COMMAND(S) TO RUN ON DEVICES ##
COMMANDS = ['show version', 'show ip route']

## GRAB ALL DEVICES WITH TAG##
url = "https://"+apicem_ip+"/api/v1/tag/association?tag={}&resourceType=network-device".format(SEARCHTAG)
response = requests.get(url,headers={"X-Auth-Token": createserviceticket(),"Content-Type": "application/json",},verify=False)
data = response.json()
tag_list = data['response']
ip_list = []

## CREATE LIST OF IP ADDRESSES/HOSTNAMES TO CONNECT TO ##
for device in tag_list:
    url = "https://" + apicem_ip + "/api/v1/network-device/{}".format(device['resourceId'])
    response = requests.get(url, headers={"X-Auth-Token": createserviceticket(), "Content-Type": "application/json", },
                            verify=False)
    data = response.json()
    deviceinfo = [data['response']['managementIpAddress'], data['response']['hostname']]
    ip_list.append(deviceinfo)

## RUN COMMANDS ON ALL DEVICES, OUTPUT TO INDIVIDUAL FILES ##
for ip in ip_list:
    ## Open output file ##
    with open(ip[1] + '.txt', 'w') as fout:

        connect_dict = {'device_type': 'cisco_ios', 'ip': ip[0], 'username': USERNAME, 'password': PASSWORD}

        try:
            net_connect = ConnectHandler(**connect_dict)
        except NetMikoTimeoutException:
            fout.write("\nUnable to connect to {}(timeout) !\n\n\n\n".format(ip))
            continue
        except NetMikoAuthenticationException:
            fout.write("\nUnable to connect to {}(authentication failure) !\n\n\n\n".format(ip))
            continue

        for command in COMMANDS:
            output = net_connect.send_command(command)
            fout.write(output)
    fout.close()

