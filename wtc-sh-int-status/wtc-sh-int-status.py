"""
Built for Warner Truck Center 6500 Migration
"""
import sys
import jtextfsm
import csv
import getpass
from netmiko import ConnectHandler
from netmiko.ssh_exception import *

DEBUG = False
DEBMAXLINES = 3

def get_show_int_status(ip, username, password):
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
            device_type='cisco_ios_telnet',
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

def main(ip, username, password):

    int_status, ssh_connection = get_show_int_status(ip, username, password)

    if int_status in ("TIMEOUT", "AUTHFAIL", "CONNECTREFUSED", "UNKNOWN"):
        print(int_status)
        sys.exit(0)

    # parse the show cdp details command using TextFSM
    re_table = jtextfsm.TextFSM(open("cisco_ios_show_interfaces_status.textfsm"))
    fsm_results = re_table.ParseText(int_status)
    headers = re_table.header

    ## REFORMAT THE OUTPUT ##
    int_status = format_fsm_output(re_table, fsm_results)

    ## Grab interface config ##
    headers.remove('DESCRIPTION')   ## Don't want duplicate description headers
    re_table = jtextfsm.TextFSM(open("cisco_ios_show_run_interface.textfsm"))
    headers += re_table.header
    headers.append('OTHER')         ## For other configuration not found with TexfFSM

    debcount = 0
    output = []
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
        output.append(newline)
        
    ## Grab MAC Addresses ##
    headers.append('MAC_ADDRESS')
    
    debcount = 0
    newoutput = []
    for line in output:
        if DEBUG == True:
            if debcount > DEBMAXLINES:
                break
            else:
                debcount += 1
                
        print("Checking mac-address-table on port {}...".format(line['PORT']))
        mac_table = ssh_connection.send_command("show mac-address-table interface {}".format(line['PORT']))
            
        re_table = jtextfsm.TextFSM(open("cisco_ios_show_mac-address-table.textfsm"))
        fsm_results = re_table.ParseText(mac_table)
        
        mac_table_formatted = format_fsm_output(re_table, fsm_results)
        macs = {'MAC_ADDRESS': ''}
        
        if not mac_table_formatted == []:
            for item in mac_table_formatted:
                macs['MAC_ADDRESS'] += item['MAC_ADDRESS']
                macs['MAC_ADDRESS'] += '\n'
                
        if not macs == {'MAC_ADDRESS': ''}:
            newline = {**line, **macs}
        else:
            newline = {**line}
            
        newoutput.append(newline)        

    # BUILD CSV ##
    ssh_connection.disconnect()
    build_csv(newoutput, headers)

if __name__ == "__main__":

    if len(sys.argv) != 3:
        print("\nplease provide the following arguments:")
        print("\tcollect-cdp-information.py <ip> <username>\n\n")
        sys.exit(0)

    target_ip = sys.argv[1]
    username = sys.argv[2]
    password = getpass.getpass("Type the password: ")

    main(target_ip, username, password)
    print("Done.")