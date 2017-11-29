import requests,json
import re
import sys
from datetime import datetime

from netmiko import ConnectHandler
from netmiko.ssh_exception import *

## Disable invalid certificate warnings for APIC ##
requests.packages.urllib3.disable_warnings()

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
    output = (f'Response HTTP Response Body: {response.content}')
    match_service_ticket = re.search('serviceTicket":"(.*cas)', output, flags=0)
    service_ticket = match_service_ticket.group(1)
    return service_ticket

## CALL APIC REST-API
def newAPICallGET(url):
    url = "https://"+APICEM_IP+"/api/v1/"+url
    try:
        response = requests.get(url,headers={"X-Auth-Token": createserviceticket(),"Content-Type": "application/json",},verify=False)
    except AttributeError:
        print("Unable to authenticate with APIC-EM, please check username/password settings.\n")
        sys.exit(0)
    except KeyboardInterrupt:
        print("User interupted connection, closing program.\n")
        sys.exit(0)    
    except Exception:
        print("Unable to connect to APIC-EM, please check network connectivity and try again.\n")
        sys.exit(0)

    return response.json()

## RUN COMMANDS ON NETWORK DEVICES
def run_commands(my_list):
    for device in my_list:
        ## Open output file ##
        with open(OUTPUTPATH + '/' + device['hostname'] + '.txt', 'w') as fout:

            connect_dict = {'device_type': 'cisco_ios', 'ip': device['ip'], 'username': USERNAME,
                            'password': PASSWORD}

            print(f"Connecting to {device['ip']}.....", end='', flush=True)
            try:
                net_connect = ConnectHandler(**connect_dict)
            except NetMikoTimeoutException:
                error = f"Unable to connect to host {device['hostname']} ({device['ip']}) (timeout)!"
                print(error)
                fout.write(error)
                continue
            except NetMikoAuthenticationException:
                error = f"Unable to connect to host {device['hostname']} ({device['ip']}) (authentication failure)!"
                print(error)
                fout.write(error)
                continue
            except ConnectionRefusedError:
                error = f"Unable to connect to host {device['hostname']} ({device['ip']}) (connection refused)!"
                print(error)
                fout.write(error)
                continue
            except KeyboardInterrupt:
                print("User interupted connection, closing program.\n")
                sys.exit(0)
            except Exception:
                error = f"Unknown error connecting to host {device['hostname']} {device['ip']}"
                print(error)
                fout.write(error)

            print("Success!", flush=True)
            for command in COMMANDS:
                print("Running Command: {}\n".format(command), flush=True)
                fout.write('\n\nRunning Command:\n'+command+'\n\n')
                output = net_connect.send_command(command)
                fout.write(output)

## GRAB ALL DEVICES WITH TAG ##
def grabdevicestag(my_list):
    ip_list = []

    ## CREATE LIST OF IP ADDRESSES/HOSTNAMES TO CONNECT TO ##
    for device in my_list:
        data = newAPICallGET(f"network-device/{device['resourceId']}")
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

def apic_run_commands(apicem_ip,apicuser,apicpass,searchtag,username,password,outputpath,commands):

    global APICEM_IP,APICUSER,APICPASS,SEARCHTAG,USERNAME,PASSWORD,OUTPUTPATH,COMMANDS
    APICEM_IP = apicem_ip
    APICUSER = apicuser
    APICPASS = apicpass
    SEARCHTAG = searchtag
    USERNAME = username
    PASSWORD = password
    OUTPUTPATH = outputpath
    COMMANDS = commands

    start_time = datetime.now()
    print("\n\n\nThank you! Gathering Output..\n\n\n")

    if SEARCHTAG == '':             # GRAB ALL DEVICES
        data = newAPICallGET('network-device')
        device_list = data['response']
        graballdevices(device_list)
    else:                           # USE SEARCH TAG
        data = newAPICallGET(f"tag/association?resourceType=network-device&tag={SEARCHTAG}")
        tag_device_list = data['response']
        grabdevicestag(tag_device_list)

    print("\nTime elapsed: {}".format(datetime.now() - start_time))
    print("Complete.")