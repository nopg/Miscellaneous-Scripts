# requirements
# python install pip
# pip install git+https://github.com/tehmaze/ipcalc   (python 3 version)

import sys
import requests,json,re
import ipcalc
import time

from operator import itemgetter
from itertools import groupby

requests.packages.urllib3.disable_warnings()
 
def delay_print(s):
    for c in s:
        sys.stdout.write( '%s' % c )
        sys.stdout.flush()
        time.sleep(0.1)

def createserviceticket():
    response = requests.post(
        url="https://"+apicem_ip+"/api/v1/ticket",
        headers={
            "Content-Type": "application/json",
        },
        verify=False,
        data=json.dumps({
            "username": 'admin',
            "password": '!Cnet2017!'
        })
    )
    output = ('Response HTTP Response Body: {content}'.format(content=response.content))
    match_service_ticket = re.search('serviceTicket":"(.*cas)', output, flags=0)
    service_ticket = match_service_ticket.group(1)
    return service_ticket

if len(sys.argv) < 2:
    print('Need arguments !')
    sys.exit(1)
 
apicem_ip = sys.argv[1] # use argument 1 in command line
print("Listing Subnets used in APIC-EM controller : "+apicem_ip)
 
url = "https://" + apicem_ip + "/api/v1/network-device/count"
resp = requests.get(url, headers={"X-Auth-Token": createserviceticket(),"Content-Type": "application/json",}, verify=False)
response_json = resp.json() # Get the json-encoded content from response with "response_json = resp.json()
count = response_json["response"]
print("Devices = {}".format(count))
interface_list = []
 
print("Collecting")
if count > 0 :
    url = "https://"+apicem_ip+"/api/v1/network-device/"
    resp = requests.get(url, headers={"X-Auth-Token": createserviceticket(), "Content-Type": "application/json", },
                        verify=False)
    response_json = resp.json()
    for device in response_json["response"]:
        id = device["id"]
        url = "https://" + apicem_ip + "/api/v1/interface/network-device/"+id
        resp = requests.get(url,    headers={"X-Auth-Token": createserviceticket(), "Content-Type": "application/json", },
                        verify=False)
        response_json = resp.json()

        for interface in response_json["response"]:
            if interface['ipv4Address'] != None: # make sure that only interfaces with an ip address, else KeyError
                interface_list.append([interface['ipv4Address'],interface['ipv4Mask']])

    subnets =[]

    for item in interface_list:
        if (item[0] != '') & (item[1] != ''):
            subnet = ipcalc.Network(item[0] + "/" + item[1])
            subnets.append( [str(subnet.network()), str(subnet.mask), str(subnet.network_long())] )
            print("")

        subnets.sort(key=itemgetter(2)) # sort by long#
        subnets = list(map(itemgetter(0), groupby(subnets))) #remove duplicates

    print("Subnets Found:")
    print("----------------------")
    print("Subnet: {0:>13}".format("Mask:"))
    print("----------------------")
    for item in subnets:
        print("{0:<15} {1:>5}".format(str(item[0]), "/"+str(item[1])))