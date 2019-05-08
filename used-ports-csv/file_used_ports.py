# Catalyst IOS based switches only. No support for NX-OS, or Routers.
import sys
import os
import asyncio
import yaml
import getpass
import csv
import jtextfsm
import logging
import tkinter as tk
from datetime import datetime

import netdev

DEBUG = 1

#netdev_logger = netdev.logger
#netdev_logger.setLevel(logging.INFO)
#netdev_logger.addHandler(logging.StreamHandler())

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
                for each in tempdevice[header]:
                     if each.startswith('-'):
                        each = '*' + each + '*'
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
    print(f"Building {filename} ...",end='')

    headers = list(output[0].keys())
    fout = open(filename, 'w')
    writer = csv.DictWriter(fout, fieldnames=headers, lineterminator='\n')
    writer.writeheader()
    writer.writerows(output)
    fout.close()
    print("Done!\n")

def main(fin,configpath,username,password,outputBox=None,root=None):

    start_time = datetime.now()
    devices = ly(fin)
    timeouts = []
    authfailed = []
    connectrefused = []
    unknownerror = []
    successes = []

    def present_output(msg):
        if not outputBox or not root:
            print(msg, end='', flush=True)
        else:
            outputBox.insert(tk.END, msg)
            outputBox.see(tk.END)
            root.update()
            print(msg, end='', flush=True)

    async def gather_used_port_output(ios, ip, output_csv):

        # Grab Switch Information
        sh_ver = await ios.send_command('show version')
        re_table = jtextfsm.TextFSM(open("cisco_ios_show_version.textfsm"))
        fsm_results = re_table.ParseText(sh_ver)
        sh_ver_formatted = await format_fsm_output(re_table, fsm_results)

        # Grab Interface List
        int_status = await ios.send_command('show interface status')
        re_table = jtextfsm.TextFSM(open("cisco_ios_show_interfaces_status_physical_only.textfsm"))
        fsm_results = re_table.ParseText(int_status)
        int_status_formatted = await format_fsm_output(re_table, fsm_results)

        hostname = sh_ver_formatted[0]['HOSTNAME']
        model = sh_ver_formatted[0]['PLATFORM']

        connected_ports_list = []
        disabled_ports_list = []
        errdisabled_ports_list = []
        notconnect_ports_list = []
        inactive_ports_list = []
        fasteth_ports_list = []
        gig_ports_list = []
        tengig_ports_list = []
        t25gig_ports_list = []

        # Create port counts
        for port in int_status_formatted:
            if port['STATUS'] == 'connected':
                connected_ports_list.append(port)
            if port['STATUS'] == 'disabled':
                disabled_ports_list.append(port)
            if port['STATUS'] == 'err-disabled':
                errdisabled_ports_list.append(port)
            if port['STATUS'] == 'notconnect':
                notconnect_ports_list.append(port)
            if port['STATUS'] == 'inactive':
                inactive_ports_list.append(port)

        for port in connected_ports_list:   
            if port['PORT'].startswith("F"):
                fasteth_ports_list.append(port) 
            if port['PORT'].startswith("G"):
                gig_ports_list.append(port)
            if port['PORT'].startswith("Twe"):
                t25gig_ports_list.append(port)
            if port['PORT'].startswith("T"):
                tengig_ports_list.append(port)

        connected_ports = len(connected_ports_list)
        disabled_ports = len(disabled_ports_list)
        errdisabled_ports = len(errdisabled_ports_list)
        notconnect_ports = len(notconnect_ports_list)
        inactive_ports = len(inactive_ports_list)
        fasteth_ports = len(fasteth_ports_list)
        gig_ports = len(gig_ports_list)
        tengig_ports = len(tengig_ports_list)
        t25gig_ports = len(t25gig_ports_list)

        # Create CSV Fields with values
        used_ports = {'Device Name': hostname, 'Model': model, 'IP Address': ip, 'Total Ports': len(int_status_formatted), 'Ports in Use/Connected': connected_ports,
                     'Disabled Ports': disabled_ports, 'Err-Disabled Ports': errdisabled_ports, "Not connected Ports": notconnect_ports, "Inactive Ports": inactive_ports,
                      "100M Port Count": fasteth_ports, "Gigabit Port Count": gig_ports, "TenGig Port Count": tengig_ports, "25G Ports": t25gig_ports}

        # Build individual switch port status CSV, update global CSV with individual values.
        if len(int_status_formatted) > 0:
            build_csv(int_status_formatted, configpath + "/" + used_ports["Device Name"] + '-' + str(datetime.now().microsecond) + '.log')
            output_csv.append(used_ports)
        else:
            print(f"Unable to find interfaces for device {hostname}")

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
        
        filename = filename + '..' + \
        str(datetime.now().year) + '-' + \
        str(datetime.now().month) + '-' + \
        str(datetime.now().day) + '--' + \
        str(datetime.now().hour) + '-' + \
        str(datetime.now().minute) + '-' + \
        str(datetime.now().second) + '.' + \
        str(datetime.now().microsecond) + '.log'
                
        successes.append( (ip , ios.base_prompt) )
                
        present_output("\nGathering device details for host " + device['host']+ ":\n")
        output = await gather_used_port_output(ios, ip, output_csv)
        present_output(output)

    # Start of MAIN function
    # BUILD DEVICE LIST TO SEND INTO run_loop() #
    device_list = []
    output_csv = []

    # Create the root folder and subfolder if it doesn't already exist
    os.makedirs(configpath, exist_ok=True)

    for type in devices:
        if devices[type]:
            for ip in devices[type]:
                if type == 'IOS':
                    device_type = 'cisco_ios'
                elif type == 'NX-OS':
                    device_type = 'cisco_nxos'             
                elif type == 'ASA':
                    device_type = 'cisco_asa'      

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