import requests,json
import re

### Disable invalid certificate warnings.
requests.packages.urllib3.disable_warnings()

apicem_ip = "devnetapi.cisco.com/sandbox/apic_em"

def createserviceticket():
    response = requests.post(
        url="https://"+apicem_ip+"/api/v1/ticket",
        headers={
            "Content-Type": "application/json",
        },
        verify=False,
        data=json.dumps({
            "username": 'devnetuser',
            "password": 'Cisco123!'
        })
    )
    output = ('Response HTTP Response Body: {content}'.format(content=response.content))
    match_service_ticket = re.search('serviceTicket":"(.*cas)', output, flags=0)
    service_ticket = match_service_ticket.group(1)
    return service_ticket

url = "https://"+apicem_ip+"/api/v1/network-device"

response = requests.get(url,headers={"X-Auth-Token": createserviceticket(),"Content-Type": "application/json",},verify=False)

data = response.json()

device_list = data['response']
for device in device_list:
    if device['reachabilityStatus'] == 'Unreachable':
        print('Hostname: %s' % device['hostname'])
        print(device['errorCode'])
        print()
