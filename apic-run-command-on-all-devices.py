import requests,json
import re

from netmiko import ConnectHandler
from netmiko.ssh_exception import *

### Disable invalid certificate warnings.
requests.packages.urllib3.disable_warnings()

APICEM_IP = "172.20.10.20"

def createserviceticket():
    response = requests.post(
        url="https://"+APICEM_IP+"/api/v1/ticket",
        headers={
            "Content-Type": "application/json",
        },
        verify=False,
        data=json.dumps({
            "USERNAME": 'admin',        ## APIC-EM USERNAME
            "PASSWORD": '!Cnet2017!'    ## APIC-EM PASSWORD
        })
    )
    output = ('Response HTTP Response Body: {content}'.format(content=response.content))
    match_service_ticket = re.search('serviceTicket":"(.*cas)', output, flags=0)
    service_ticket = match_service_ticket.group(1)
    return service_ticket

## LOGIN INFORMATION FOR NETWORK DEVICES ##
USERNAME = 'admin'
PASSWORD = '!Cnet2017!'

## COMMAND(S) TO RUN ON DEVICES ##
commands = ['show version', 'show ip route']

## GRAB ALL DEVICES ##
url = "https://"+APICEM_IP+"/api/v1/network-device"
response = requests.get(url,headers={"X-Auth-Token": createserviceticket(),"Content-Type": "application/json",},verify=False)
data = response.json()
device_list = data['response']

for device in device_list:
    ip = device['managementIpAddress']

    ## Open output file ##
    with open(device['hostname'], 'w') as fout:

        connect_dict = {'device_type': 'cisco_ios', 'ip': ip, 'USERNAME': USERNAME, 'PASSWORD': PASSWORD}

        try:
            net_connect = ConnectHandler(**connect_dict)
        except NetMikoTimeoutException:
            fout.write("\nUnable to connect to {}(timeout) !\n\n\n\n".format(ip))
            continue
        except NetMikoAuthenticationException:
            fout.write("\nUnable to connect to {}(authentication failure) !\n\n\n\n".format(ip))
            continue

        for command in commands:
            output = net_connect.send_command(command)
            fout.write(output)
    fout.close()

