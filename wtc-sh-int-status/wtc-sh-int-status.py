"""
Built for Warner Truck Center 6500 Migration
"""
import sys
import jtextfsm
import csv
import getpass
from datetime import datetime
from netmiko import ConnectHandler
from netmiko.ssh_exception import *

DEBUG = False
DEBMAXLINES = 3

def get_show_int_status(device_type, ip, username, password):
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
        return "TIMEOUT", None
    except NetMikoAuthenticationException:
        print("\nSSH authentication failed for device: {}\n".format(ip))
        return "AUTHFAIL", None
    except ConnectionRefusedError:
        print("\nConnection refused for device: {}\n".format(ip))
        return "CONNECTREFUSED", None
    except KeyboardInterrupt:
        print("\nUser interupted connection, closing program.\n")
        sys.exit(0)
    except Exception:
        print("\nUnknown error connecting to device: {}\n".format(ip))
        return "UNKNOWN", None

    # execute the show cdp neighbor detail command
    # we increase the delay_factor for this command, because it take some time if many devices are seen by CDP
    result = ssh_connection.send_command("show interface status", delay_factor=2)

    # close SSH connection
    #ssh_connection.disconnect()

    return result, ssh_connection

def format_fsm_output(re_table, fsm_results):
    #   FORMAT FSM OUTPUT(LIST OF LIST) INTO PYTHON LIST OF DICTIONARY VALUES BASED ON TEXTFSM TEMPLATE #
    result = []
    for item in fsm_results:
        tempdevice = {}
        for position, header in enumerate(re_table.header):
            tempdevice[header] = item[position]
        ## EXCEL DOESN'T LIKE FIELDS STARTING WITH --- ##
            if '---' in tempdevice[header]:
                tempdevice[header] = '*' + tempdevice[header] + '*'
        result.append(tempdevice)

    return result

def build_csv(output, headers):
    fout = open('int-status-output.csv', 'w')
    writer = csv.DictWriter(fout, fieldnames=headers, lineterminator='\n')
    writer.writeheader()
    writer.writerows(output)
    fout.close()

def check_arp_table(arp_table_formatted, mac_address):
    for ip in arp_table_formatted:
        if ip['MAC'] == mac_address:
            return ip['ADDRESS'], ip['MACVLAN']
        else:
            pass
    return 'not found', ''


def main(device_type, ip, username, password):

    int_status, ssh_connection = get_show_int_status(device_type, ip, username, password)

    if int_status in ("TIMEOUT", "AUTHFAIL", "CONNECTREFUSED", "UNKNOWN"):
        print(int_status)
        sys.exit(0)

    ## GRAB ARP Table ##

    arp_table = ssh_connection.send_command("show ip arp")

    re_table = jtextfsm.TextFSM(open("cisco_ios_show_ip_arp.textfsm"))
    fsm_results = re_table.ParseText(arp_table)
    arp_table_formatted = format_fsm_output(re_table, fsm_results)

    # GRAB INTERFACE STATUS ##
    re_table = jtextfsm.TextFSM(open("cisco_ios_show_interfaces_status.textfsm"))
    fsm_results = re_table.ParseText(int_status)

    ## REFORMAT THE OUTPUT ##
    int_status = format_fsm_output(re_table, fsm_results)

    ## Grab interface config ##
    debcount = 0
    tempoutput1 = []
    for line in int_status:
        if DEBUG == True:
            if debcount > DEBMAXLINES:
                break
            else:
                debcount += 1
                
        print("Checking config on port {}...".format(line['PORT']))

        port_config = ssh_connection.send_command("show run int {}".format(line['PORT']))

        re_table = jtextfsm.TextFSM(open("cisco_ios_show_run_interface.textfsm"))
        fsm_results = re_table.ParseText(port_config)
        
        portconfig = format_fsm_output(re_table, fsm_results)

        if not portconfig == []:
            newline = {**line, **portconfig[0]}     ## Combine dictionaries
        else:
            newline = {**line}
        
        newline['OTHER'] = port_config          ## Add full config to catch anything extra (need to update)
        tempoutput1.append(newline)
        
    ## Grab MAC Addresses ##
    debcount = 0
    tempoutput2 = []
    for line in tempoutput1:
        if DEBUG == True:
            if debcount > DEBMAXLINES:
                break
            else:
                debcount += 1
                
        print("Checking mac-address-table on port {}...".format(line['PORT']))
        mac_table = ssh_connection.send_command("show mac-address-table interface {}".format(line['PORT']))
            
        re_table = jtextfsm.TextFSM(open("cisco_ios_show_mac_address_table.textfsm"))
        fsm_results = re_table.ParseText(mac_table)
        
        mac_table_formatted = format_fsm_output(re_table, fsm_results)
        macs = {'MAC_ADDRESS': '', 'IP': '', 'MACVLAN': ''}
        
        if mac_table_formatted.__len__() == 1:
            macs['MAC_ADDRESS'] = mac_table_formatted[0]['MAC_ADDRESS']
            macs['IP'], macs['MACVLAN'] = check_arp_table(arp_table_formatted, macs['MAC_ADDRESS'])

        elif not mac_table_formatted == []:
            for item in mac_table_formatted:
                macs['MAC_ADDRESS'] += item['MAC_ADDRESS']
                macs['MAC_ADDRESS'] += '\n'

                ip,vlan = check_arp_table(arp_table_formatted, item['MAC_ADDRESS'])
                macs['IP'] += ip
                macs['IP'] += '\n'
                macs['MACVLAN'] += vlan
                macs['MACVLAN'] += '\n'

        newline = {**line, **macs}

        tempoutput2.append(newline)


    # BUILD CSV ##
    headers = list(tempoutput2[0].keys())
    ssh_connection.disconnect()
    build_csv(tempoutput2, headers)
    
if __name__ == "__main__":

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

    start_time = datetime.now()
    main(device_type, target_ip, username, password)
    print()
    print("Done.")
    print("Time elapsed: {}".format(datetime.now() - start_time))