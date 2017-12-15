import sys
from datetime import datetime
import requests,json
import re
import tkinter as tk

from netmiko import ConnectHandler
from netmiko.ssh_exception import *

## Disable invalid certificate warnings for APIC ##
requests.packages.urllib3.disable_warnings()

## MAIN ##

def apic_run_commands(apicem_ip,apicuser,apicpass,searchtag,username,password,outputpath,commands,outputBox=None,root=None):

    ###################################
    ## INTERNAL FUNCTION DEFINITIONS ##
    ###################################

    ## AUTH WITH APIC-EM ##
    def createserviceticket():
        response = requests.post(
            url="https://" + APICEM_IP + "/api/v1/ticket",
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
        url = "https://" + APICEM_IP + "/api/v1/" + url
        try:
            response = requests.get(url, headers={"X-Auth-Token": createserviceticket(),
                                                  "Content-Type": "application/json", }, verify=False)
        except AttributeError:
            print("Unable to authenticate with APIC-EM, please check username/password settings.\n")
            sys.exit(0)
        except KeyboardInterrupt:
            print("User interrupted connection, closing program.\n")
            sys.exit(0)
        except Exception:
            print("Unable to connect to APIC-EM, please check network connectivity and try again.\n")
            sys.exit(0)

        return response.json()

    ## RUN COMMANDS ON NETWORK DEVICES
    def run_commands(my_list):
        for device in my_list:

            connect_dict = {'device_type': 'cisco_ios', 'ip': device['ip'], 'username': USERNAME,
                            'password': PASSWORD}

            present_output("\nConnecting to {}.....\n".format(device['ip']))

            try:
                net_connect = ConnectHandler(**connect_dict)
            except NetMikoTimeoutException:
                present_output("Unable to connect to host {} ({}) (timeout!".format(device['hostname'], device['ip']))
                continue
            except NetMikoAuthenticationException:
                present_output("Unable to connect to host {} ({}) (authentication failure)!".format(device['hostname'],
                                                                                                    device['ip']))
                continue
            except ConnectionRefusedError:
                present_output("Unable to connect to host {} ({}) (connection refused)!".format(device['hostname'],
                                                                                                device['ip']))
                continue
            except KeyboardInterrupt:
                print("User interupted connection, closing program.\n")
                sys.exit(0)
            except Exception:
                present_output("Unknown error connecting to host {} ({})".format(device['hostname'],
                                                                                 device['ip']))
                continue

            present_output("Success!")

            if outputpath == '':
                if device_type == "cisco_nxos":
                    pass
                else:
                    for command in COMMANDS:
                        present_output("\n\nRunning Command: {}\n".format(command))
                        fout.write("\n\nRunning Command:\n" + command + "\n\n")

                        output = net_connect.send_command(command)
                        present_output(output)
            else:
                try:
                    ## Open output file ##
                    with open(OUTPUTPATH + '/' + device['hostname'] + '.txt', 'w') as fout:
                        if device_type == "cisco_nxos":
                            pass
                        else:
                            for command in COMMANDS:
                                present_output("\n\nRunning Command: {}\n".format(command))
                                fout.write("\n\nRunning Command:\n" + command + "\n\n")

                                output = net_connect.send_command(command)
                                fout.write(output)
                                present_output(output)
                except:
                    present_output("\nInvalid destination folder!\nContinuing....")

                    output = net_connect.send_config_set(COMMANDS)

                    present_output(output)

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
            temp_device = {'ip': device['managementIpAddress'], 'hostname': device['hostname']}
            ip_list.append(temp_device)

        run_commands(ip_list)

    def present_output(msg):
        if not outputBox or not root:
            print(msg, end='', flush=True)
        else:
            outputBox.insert(tk.END, msg)
            outputBox.see(tk.END)
            root.update()
            print(msg, end='', flush=True)

    ###################
    ## MAIN FUNCTION ##
    ###################
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
    present_output("\n\n\nThank you! Gathering Output..\n\n\n")

    if SEARCHTAG == '':             # GRAB ALL DEVICES
        data = newAPICallGET('network-device')
        device_list = data['response']
        graballdevices(device_list)
    else:                           # USE SEARCH TAG
        data = newAPICallGET(f"tag/association?resourceType=network-device&tag={SEARCHTAG}")
        tag_device_list = data['response']
        grabdevicestag(tag_device_list)

    present_output("\nTime elapsed: {}".format(datetime.now() - start_time))
    present_output("\nComplete.\n\n\nComplete!")
