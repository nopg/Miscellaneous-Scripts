"""
Built for Warner Truck Center 6500 Migration
"""
import sys
import jtextfsm
import csv
import getpass
import re
import requests
from datetime import datetime
from netmiko import ConnectHandler
from netmiko.ssh_exception import *

DEBUG = False
DEBMAXLINES = 10
MACVENDOR = False

def get_connection(device_type, ip, username, password):
    """
    get the CDP neighbor detail from the device using SSH

    :param ip: IP address of the device
    :param username: username used for the authentication
    :param password: password used for the authentication
    :param enable_secret: enable secret
    :return:
    """
    # establish a connection to the device
    try:
        ssh_connection = ConnectHandler(
            device_type=device_type,
            ip=ip,
            username=username,
            password=password,
        )
        ssh_connection.enable()
    except NetMikoTimeoutException:
        print("\nSSH session timed trying to connect to the device: {}\n".format(ip))
        return "TIMEOUT"
    except NetMikoAuthenticationException:
        print("\nSSH authentication failed for device: {}\n".format(ip))
        return "AUTHFAIL"
    except ConnectionRefusedError:
        print("\nConnection refused for device: {}\n".format(ip))
        return "CONNECTREFUSED"
    except KeyboardInterrupt:
        print("\nUser interupted connection, closing program.\n")
        sys.exit(0)
    except Exception:
        print("\nUnknown error connecting to device: {}\n".format(ip))
        return "UNKNOWN"

    return ssh_connection

def format_fsm_output(re_table, fsm_results):
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
            if  tempdevice[header].startswith('-'):
                tempdevice[header] = '*' + tempdevice[header] + '*'
        result.append(tempdevice)

    return result

def build_csv(output):
    """
    BUILD CSV BASED ON AN EXISTING DICTIONARY

    :param output: existing dictionary to be written
    :return:
    """
    print("Building CSV...")
    headers = list(output[0].keys())
    fout = open('int-status-output.csv', 'w')
    writer = csv.DictWriter(fout, fieldnames=headers, lineterminator='\n')
    writer.writeheader()
    writer.writerows(output)
    fout.close()

def correlate_arp_and_mac(arp_table, mac_table, oldoutput):
    """
    CORRELATE ARP AND MAC TABLES FOR EACH INTERFACE ON DEVICE

    :param arp_table: arp table in dictionary format
    :param mac_table: mac table in dictionary format
    :param ouldoutput: existing output to be written to CSV
    :return output: updated output including arp/mac entries found
    """
    global MACVENDOR

    output = []
    for line in oldoutput:
        mydict = {'MAC_ADDRESS': '', 'IP': '', 'MACVLAN': '', 'MAC_VENDOR': ''}
        for mac in mac_table:
            if mac['DESTINATION_PORT'] == line['PORT']:
                mydict['MAC_ADDRESS'] += mac['MAC_ADDRESS']
                mydict['MAC_ADDRESS'] += '\n'

                # CALL API FOR MACVENDORS TO GRAB THE MAC VENDOR #
                if MACVENDOR == True:
                    print("Grabbing MAC Vendor info for mac: {}".format(mac['MAC_ADDRESS']))
                    url = 'http://api.macvendors.com/' + mac['MAC_ADDRESS']
                    response = requests.get(url=url)
                    mydict['MAC_VENDOR'] += response.text
                    mydict['MAC_VENDOR'] += '\n'

                # Search ARP for this MAC #
                for ip in arp_table:
                    if ip['MAC'] == mac['MAC_ADDRESS']:
                        mydict['IP'] += ip['ADDRESS']
                        mydict['IP'] += '\n'
                        mydict['MACVLAN'] += ip['MACVLAN']
                        mydict['MACVLAN'] += '\n'

                if mydict['IP'] == '':
                    mydict['IP'] = 'not found\n'

        # EXCEL DOESN'T LIKE NEWLINES IN SOME CASES #
        mydict['IP'] = mydict['IP'].rstrip()
        mydict['MACVLAN'] = mydict['MACVLAN'].rstrip()
        mydict['MAC_ADDRESS'] = mydict['MAC_ADDRESS'].rstrip()
        mydict['MAC_VENDOR'] = mydict['MAC_VENDOR'].rstrip()

        newline = {**line, **mydict}
        output.append(newline)

    return output

def main(device_type, ip, username, password):

    # GET CONNECTION ##
    ssh_connection = get_connection(device_type, ip, username, password)
    if ssh_connection in ("TIMEOUT", "AUTHFAIL", "CONNECTREFUSED", "UNKNOWN"):
        print(ssh_connection)
        sys.exit(0)

    # GRAB ARP TABLE #
    arp_table = ssh_connection.send_command("show ip arp", delay_factor=2)
    re_table = jtextfsm.TextFSM(open("cisco_ios_show_ip_arp.textfsm"))
    fsm_results = re_table.ParseText(arp_table)
    arp_table_formatted = format_fsm_output(re_table, fsm_results)

    # GRAB MAC TABLE #
    arp_table = ssh_connection.send_command("show mac-address-table", delay_factor=2)
    re_table = jtextfsm.TextFSM(open("cisco_ios_show_mac_address_table.textfsm"))
    fsm_results = re_table.ParseText(arp_table)
    mac_table_formatted = format_fsm_output(re_table, fsm_results)

    # GRAB INTERFACE STATUS #
    int_status = ssh_connection.send_command("show interface status", delay_factor=2)
    re_table = jtextfsm.TextFSM(open("cisco_ios_show_interfaces_status.textfsm"))
    fsm_results = re_table.ParseText(int_status)
    int_status_formatted = format_fsm_output(re_table, fsm_results)

    # GRAB CDP NEIGHBORS #
    cdp_neighbors = ssh_connection.send_command("show cdp neighbor detail", delay_factor=2)
    re_table = jtextfsm.TextFSM(open("show_cdp_neighbor_detail-m.textfsm"))
    fsm_results = re_table.ParseText(cdp_neighbors)
    cdp_neighbors = format_fsm_output(re_table, fsm_results)

    # GRAB INTERFACE CONFIG #
    debcount = 0
    tempoutput1 = []
    for line in int_status_formatted:
        if DEBUG == True:
            if debcount > DEBMAXLINES:
                break
            else:
                debcount += 1
                
        print("Checking config on port {}...".format(line['PORT']))

        # PARSE INTERFACE CONFIG VIA FSM
        port_config = ssh_connection.send_command("show run int {}".format(line['PORT']))
        re_table = jtextfsm.TextFSM(open("cisco_ios_show_run_interface.textfsm"))
        fsm_results = re_table.ParseText(port_config)
        portconfig = format_fsm_output(re_table, fsm_results)

        if not portconfig == []:
            newline = {**line, **portconfig[0]}     # Combine dictionaries
        else:
            newline = {**line}
        
        newline['OTHER'] = port_config          # Add full config to catch anything extra (update to only extra's)
        tempoutput1.append(newline)

    # CORRELATE ARP AND MAC TABLES #
    tempoutput2 = correlate_arp_and_mac(arp_table_formatted, mac_table_formatted, tempoutput1)

    # ADD CDP INFORMATION #
    myoutput = []
    for port in tempoutput2:
        mydict = {'CDP_MANAGEMENT_IP': '', 'CDP_NEIGHBOR': '', 'REMOTE_PORT': '', 'MODEL': ''}
        for neighbor in cdp_neighbors:
            # TRUNCATE 'GigabitEthernet1/1' TO 'Gi1/1' TO MATCH INT STATUS PORT NAME#
            e = neighbor['LOCAL_PORT']
            type = e[0:2]                           # FIRST TWO CHARACTERS #
            numindex = re.search('\d', e).start()   # INDEX OF FIRST DIGIT #
            num = e[numindex:]                      # EVERYTHING AFTER FIRST DIGIT #
            local_port = type + num                 # Gi + 1/1

            # MATCH EXCEL HEADERS TO TEXTFSM HEADERS
            if port['PORT'] == local_port:
                mydict['CDP_MANAGEMENT_IP'] += neighbor['MANAGEMENT_IP']
                mydict['CDP_MANAGEMENT_IP'] += '\n'
                mydict['CDP_NEIGHBOR'] += neighbor['DESTINATION_HOST']
                mydict['CDP_NEIGHBOR'] += '\n'
                mydict['REMOTE_PORT'] += neighbor['REMOTE_PORT']
                mydict['REMOTE_PORT'] += '\n'
                mydict['MODEL'] += neighbor['PLATFORM']
                mydict['MODEL'] += '\n'

        # EXCEL DOESN'T LIKE NEWLINES IN SOME CASES #
        mydict['CDP_MANAGEMENT_IP'] = mydict['CDP_MANAGEMENT_IP'].rstrip()
        mydict['CDP_NEIGHBOR'] = mydict['CDP_NEIGHBOR'].rstrip()
        mydict['REMOTE_PORT'] = mydict['REMOTE_PORT'].rstrip()
        mydict['MODEL'] = mydict['MODEL'].rstrip()

        newline = {**port, **mydict}
        myoutput.append(newline)

    # BUILD CSV ##
    ssh_connection.disconnect()
    build_csv(myoutput)
    
if __name__ == "__main__":

    MACVENDOR = False

    if len(sys.argv) != 4:
        print("\nplease provide the following arguments:")
        print("\tcollect-cdp-information.py <telnet or ssh> <ip> <username>\n\n")
        sys.exit(0)

    ssh_or_telnet = sys.argv[1]
    if ssh_or_telnet == 'ssh':
        device_type = 'cisco_ios'
    elif ssh_or_telnet == 'telnet':
        device_type = 'cisco_ios_telnet'
    else:
        print("\nUnknown connection type '{}', please provide the following arguments:".format(ssh_or_telnet))
        print("\tcollect-cdp-information.py <telnet or ssh> <ip> <username>\n\n")
        sys.exit(0)

    target_ip = sys.argv[2]
    username = sys.argv[3]
    password = getpass.getpass("Type the password: ")

    while True:
        macvendor = input("Pull MAC Vendor information? (y/n)")
        if macvendor == 'y':
            MACVENDOR = True
            break
        elif macvendor == 'n':
            MACVENDOR = False
            break

    start_time = datetime.now()
    print("Thank you! Pulling data...")

    # RUN PROGRAM #
    main(device_type, target_ip, username, password)

    print()
    print("Done.")
    print("Time elapsed: {}\n".format(datetime.now() - start_time))