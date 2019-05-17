# Catalyst IOS based switches only. No support for NX-OS, or Routers.
import sys
import os
import asyncio
import yaml
import getpass
import csv
import logging
import tkinter as tk
from datetime import datetime

import netdev
import jtextfsm

DEBUG = 1

def ly(filename):
    try:
        with open(filename) as _:
            return yaml.load(_)
    except:
        if not DEBUG:
            print("Invalid device file!")
            sys.exit(0)
        else:
            return { 'IOS': [filename] }

async def format_fsm_output(re_table, fsm_results):
    """
    FORMAT FSM OUTPUT(LIST OF LIST) INTO PYTHON LIST OF DICTIONARY VALUES BASED ON TEXTFSM TEMPLATE

    :param re_table: re_table from generic fsm search
    :param fsm_results: fsm results from generic fsm search
    :return result: updated list of dictionary values
    """
    result = []
    for item in fsm_results:
        tempdevice = {}
        for position, header in enumerate(re_table.header):
            tempdevice[header] = item[position]
        ## EXCEL DOESN'T LIKE FIELDS STARTING WITH '-' ##
            if isinstance(tempdevice[header], list):
                # Won't effect excel
                pass
            elif tempdevice[header].startswith('-'):
                tempdevice[header] = '*' + tempdevice[header] + '*'
        result.append(tempdevice)

    return result

def build_csv(output, filename):
    """
    BUILD CSV BASED ON AN EXISTING DICTIONARY

    :param output: existing dictionary to be written
    :return:
    """
    filename = filename + ".csv"
    print(f"Building {filename} ...")

    headers = list(output[0].keys())
    fout = open(filename, 'w')
    writer = csv.DictWriter(fout, fieldnames=headers, lineterminator='\n')
    writer.writeheader()
    writer.writerows(output)
    fout.close()


def main(fin,configpath,username,password,outputBox=None,root=None):

    start_time = datetime.now()
    devices = ly(fin)
    timeouts = []
    authfailed = []
    connectrefused = []
    unknownerror = []
    successes = []

    # Print only to terminal or to both popupbox and terminal
    def present_output(msg):
        if not outputBox or not root:
            print(msg, end='', flush=True)
        else:
            outputBox.insert(tk.END, msg)
            outputBox.see(tk.END)
            root.update()
            print(msg, end='', flush=True)

    async def gather_used_port_output(ios, ip, device_type, output_csv):

        if device_type == "cisco_ios":
            SHVERFSM = "cisco_ios_show_version.textfsm"
            INTSTATUSFSM = "cisco_ios_show_interfaces_status_physical_only.textfsm"

        elif device_type == "cisco_nxos":
            SHVERFSM = "cisco_nxos_show_version.textfsm"
            INTSTATUSFSM = "cisco_nxos_show_interface_status_physical_only.textfsm"

        # Grab Switch Information
        sh_ver = await ios.send_command('show version')
        re_table = jtextfsm.TextFSM(open(SHVERFSM))
        fsm_results = re_table.ParseText(sh_ver)
        sh_ver_formatted = await format_fsm_output(re_table, fsm_results)

        # Grab Interface List
        int_status = await ios.send_command('show interface status')
        re_table = jtextfsm.TextFSM(open(INTSTATUSFSM))
        fsm_results = re_table.ParseText(int_status)
        int_status_formatted = await format_fsm_output(re_table, fsm_results)

        hostname = ios.base_prompt

        if not sh_ver_formatted:
            # Error grabbing info, mark everything unknown and record
            used_ports = {'Device Name': hostname, 'Model': "unknown", 'IP Address': ip, 'Total Ports': "unknown", 'Connected Ports': "unknown",
                     'Disabled Ports': "unknown", 'Err-Disabled Ports': "unknown", "Not connected Ports": "unknown", "Inactive Ports": "unknown",
                      "100M Port Count": "unknown", "1Gig Port Count": "unknown", "TenGig Port Count": "unknown", "25G Ports": "unknown", "40G Ports": "unknown", "100G Ports": "unknown"}
            output_csv.append(used_ports)
            return f"Error grabbing information for (probably unsupported) device: {ip}, skipping interface check.\n"
        else:
            # Info found, extract Model information and continue
            if device_type == "cisco_nxos":
                model = "Nexus " + sh_ver_formatted[0]['PLATFORM']
            else: 
                model = sh_ver_formatted[0]['PLATFORM']

        if not int_status_formatted:
            # Create CSV Fields with unknown values
            used_ports = {'Device Name': hostname, 'Model': model, 'IP Address': ip, 'Total Ports': "unknown", 'Connected Ports': "unknown",
                        'Disabled Ports': "unknown", 'Err-Disabled Ports': "unknown", "Not connected Ports": "unknown", "Inactive Ports": "unknown",
                        "100M Port Count": "unknown", "1Gig Port Count": "unknown", "TenGig Port Count": "unknown", "25G Ports": "unknown", "40G Ports": "unknown", "100G Ports": "unknown"}
            output_csv.append(used_ports)
            return f"Unable to find interfaces for (probably unsupported) device {hostname}\n"

        connected_ports_list = []
        disabled_ports_list = []
        errdisabled_ports_list = []
        notconnect_ports_list = []
        inactive_ports_list = []
        fasteth_ports_list = []
        gig_ports_list = []
        tengig_ports_list = []
        t25gig_ports_list = []
        fortygig_ports_list = []
        hungig_ports_list = []

        # Create port counts
        for port in int_status_formatted:
            if port['STATUS'] == 'connected':
                connected_ports_list.append(port)
            elif port['STATUS'] == 'disabled':
                disabled_ports_list.append(port)
            elif port['STATUS'] == 'err-disabled':
                errdisabled_ports_list.append(port)
            elif 'notconnec' in port['STATUS']:
                notconnect_ports_list.append(port)
            elif port['STATUS'] == 'inactive' or port['STATUS'] == 'sfpAbsent':
                inactive_ports_list.append(port)

        for port in connected_ports_list:   
            if "1000" in port['SPEED']:
                gig_ports_list.append(port) 
            elif "10G" in port['SPEED']:
                tengig_ports_list.append(port)
            elif "40G" in port['SPEED']:
                fortygig_ports_list.append(port)
            elif "100G" in port['SPEED']:
                hungig_ports_list.append(port)
            elif "100" in port['SPEED']:
                fasteth_ports_list.append(port)

        connected_ports = len(connected_ports_list)
        disabled_ports = len(disabled_ports_list)
        errdisabled_ports = len(errdisabled_ports_list)
        notconnect_ports = len(notconnect_ports_list)
        inactive_ports = len(inactive_ports_list)
        fasteth_ports = len(fasteth_ports_list)
        gig_ports = len(gig_ports_list)
        tengig_ports = len(tengig_ports_list)
        t25gig_ports = len(t25gig_ports_list)
        fortygig_ports = len(fortygig_ports_list)
        hungig_ports = len(hungig_ports_list)

        # Build individual switch port status CSV, update global CSV with individual values.
        used_ports = {'Device Name': hostname, 'Model': model, 'IP Address': ip, 'Total Ports': len(int_status_formatted), 'Connected Ports': connected_ports,
                    'Disabled Ports': disabled_ports, 'Err-Disabled Ports': errdisabled_ports, "Not connected Ports": notconnect_ports, "Inactive Ports": inactive_ports,
                    "100M Port Count": fasteth_ports, "1Gig Port Count": gig_ports, "TenGig Port Count": tengig_ports, "25G Ports": t25gig_ports, 
                    "40G Ports": fortygig_ports, "100G Ports": hungig_ports}

        build_csv(int_status_formatted, configpath + "/" + used_ports["Device Name"] + '-' + str(datetime.now().microsecond) + '.log')
        output_csv.append(used_ports)


        return f"Finished with host: {ip}\n"

    async def connect_and_run(device, configpath, output_csv):

        present_output("\nConnecting to {}.....\n".format(device['host']))
        try: 
            ios = netdev.create(**device)
            await ios.connect()
        except netdev.exceptions.TimeoutError as e:
            timeouts.append(device['host'])
            present_output("\nERROR =  {}\n".format(e))
            return
        except netdev.exceptions.DisconnectError as e:
            authfailed.append(device['host'])
            present_output("\nERROR = {}\n".format(e))
            return
        except netdev.exceptions.CommitError as e:
            unknownerror.append(device['host'])
            present_output("\nERROR = {}\n".format(e))
            return
        except Exception as e:
            unknownerror.append(device['host'])
            present_output("\nERROR = {}\n".format(e))
            return

        filename = ios.base_prompt
        ip = device['host'] 
                
        successes.append( (ip , ios.base_prompt) )
                
        present_output("\nGathering device details for host " + device['host']+ ":\n")
        output = await gather_used_port_output(ios, ip, device["device_type"], output_csv)
        present_output(output)

    # Start of MAIN function
    # BUILD DEVICE LIST TO SEND INTO run_loop() #
    device_list = []
    output_csv = []

    # Create the root folder and subfolder if it doesn't already exist
    os.makedirs(configpath, exist_ok=True)

    for dtype in devices:
        if devices[dtype]:
            for ip in devices[dtype]:
                if dtype == 'IOS':
                    device_type = 'cisco_ios'
                elif dtype == 'NX-OS':
                    device_type = 'cisco_nxos'             
                else:
                    present_output(f"Invalid device type \'{dtype}\'. Supported device types are \'IOS:\' or \'NX-OS:\'. Exiting..\n")     
                    sys.exit(0)
                if ip:
                    device_list.append( {'username': username, 'password': password, 'device_type': device_type, 'host': ip} )

    # RUN LOOP #
    loop = asyncio.get_event_loop()
    tasks = [connect_and_run(device, configpath, output_csv) for device in device_list]
    loop.run_until_complete(asyncio.wait(tasks))

    if len(successes) > 0:
        build_csv(output_csv, configpath + "/Used-Port-Inventory" )
    else:
        present_output("\n*********************************\n\n")
        print("\nNot able to connect to any devices. No output has been created.\n")
        present_output("\n*********************************\n\n")

    present_output("\n------------------------------\n\n")
    present_output("\n\nStats from last run:")
    
    present_output("\n\nDevices timed out: ")
    [present_output("\n" + each) for each in timeouts]

    present_output("\n\nAuthentication failures:")
    [present_output("\n" + each) for each in authfailed]
        
    present_output("\n\nConnection Refused:")
    [present_output("\n" + each) for each in connectrefused]
        
    present_output("\n\nUnknown Error:")
    [present_output("\n" + each) for each in unknownerror]
        
    present_output("\n\nSuccessful: ")
    [present_output("\n{:15s} {:15s}".format(addr,fname)) for addr,fname in successes]
        
    present_output("\n\nTime elapsed: {}\n\n".format(datetime.now() - start_time))

    present_output(f"\n\nComplete. Check {configpath} folder for output.\n")

    present_output("\n------------------------------\n\n")

    return

if __name__ == "__main__":

    if len(sys.argv) != 4:
        print("\nplease provide the following arguments:")
        print("\tpython3 file_run_commands.py <device-file.yml> <output folder path> <username>\n\n")
        sys.exit(0)

    device_file = sys.argv[1]
    configpath = sys.argv[2]
    username = sys.argv[3]

    password = getpass.getpass("Type the password: ")

    main(device_file, configpath, username, password)