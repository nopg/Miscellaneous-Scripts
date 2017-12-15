import requests,json
import re

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
            "username": 'admin',
            "password": 'xxxx'
        })
    )
    output = ('Response HTTP Response Body: {content}'.format(content=response.content))
    match_service_ticket = re.search('serviceTicket":"(.*cas)', output, flags=0)
    service_ticket = match_service_ticket.group(1)
    return service_ticket

def newAPICallGET(url):
    url = "https://"+apicem_ip+"/api/v1/"+url

    response = requests.get(url,headers={"X-Auth-Token": createserviceticket(),"Content-Type": "application/json",},verify=False)

    return response.json()

def newAPICallDELETE(url):
    url = "https://"+apicem_ip+"/api/v1/"+url

    response = requests.delete(url,headers={"X-Auth-Token": createserviceticket(),"Content-Type": "application/json",},verify=False)

    return response.json()


## DELETE INVENTORY DEVICES ##
data = newAPICallGET('network-device')

device_list = data['response']
for device in device_list:
    id = device['id']
    response = newAPICallDELETE('network-device/'+id)
    print("Device: {} deleted".format(device['hostname']))
    print("\tResponse = {}".format(response))

print("==========================================================")

## DELETE EASYQOS POLICIES ##
data = newAPICallGET('policy')
policy_list = data['response']
for policy in policy_list:
    policyScope = policy['policyScope']
    if policyScope != "CVD":
        response = newAPICallDELETE('policy/?policyScope='+policyScope)
        print("Policy {} in Scope {} deleted".format(policy['policyName'], policyScope))
        print("\tResponse = {}".format(response))
    else: print("Policy {} in Scope {} NOT DELETED".format(policy['policyName'], policyScope))

print("==========================================================")

## DELETE EASYQOS POLICY SCOPES ##
data = newAPICallGET('policy/tag')
policy_list = data['response']
for policy in policy_list:
    policyScope = policy['policyTag']
    response = newAPICallDELETE('policy/tag/?policyTag='+policyScope)
    print("Policy Scope {} deleted".format(policyScope))
    print("\tResponse = {}".format(response))

print("==========================================================")

## DELETE PNP PROJECTS ##
data = newAPICallGET('pnp-project')

project_list = data['response']
for project in project_list:
    id = project['id']
    response = newAPICallDELETE('pnp-project/'+id)
    print("Project: {} deleted".format(project['siteName']))
    print("\tResponse = {}".format(response))

print("==========================================================")

## DELETE PNP DEVICES ##
data = newAPICallGET('pnp-device')

device_list = data['response']
for device in device_list:
    id = device['id']
    response = newAPICallDELETE('pnp-device/'+id)
    print("Device: {} deleted".format(device['siteName']))
    print("\tResponse = {}".format(response))

