import sys
import yaml
import getpass
import dictdiffer
import jtextfsm
from datetime import datetime

from netmiko import ConnectHandler
from netmiko.ssh_exception import *

def ly(filename):
    try:
        with open(filename) as _:
            return yaml.load(_)
    except:
        print("Invalid device file!")
        sys.exit(0)

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

        result.append(tempdevice)

    return result

def connect(device_list,username,password):

    start_time = datetime.now()
    timeouts = []
    authfailed = []
    connectrefused = []
    unknownerror = []
    successes = []

    def output2():
        print("\n\n\n\n\n\n")
        print("Devices timed out: ")
        for each in timeouts:
            print(each)
        print()
        print("Authentication failures:")
        for each in authfailed:
            print(each)
        print()
        print("Connection Refused:")
        for each in connectrefused:
            print(each)
        print()
        print("Unknown Error:")
        for each in unknownerror:
            print(each)
        print()
        print("Successful: ")
        for addr,fname in successes:
            print("{:15s} {:15s}".format(addr,fname))
        print()
        print("Time elapsed: {}".format(datetime.now() - start_time))

    ## GRAB MASTER DATABASE ##
    connect_dict = {'device_type': 'cisco_ios', 'ip': device_list['MASTER'][0], 'username': username, 'password': password, 'secret': '6R1mL0k!'}
    net_connect = ConnectHandler(**connect_dict)  
    master = net_connect.send_command("show ip ospf database")
    re_table = jtextfsm.TextFSM(open("cisco_ios_show_ip_ospf_database.textfsm"))
    fsm_results = re_table.ParseText(master)
    master_ospf = format_fsm_output(re_table, fsm_results)

    with open("output/MASTER.log", "w") as fout:
        fout.write(master)

    for type in device_list:
        for ip in device_list[type]:
            if type == 'IOS':
                device_type = 'cisco_ios'
            elif type == 'NX-OS':
                device_type = 'cisco_nxos'
            elif type == 'MASTER':
                continue
            else: device_type = 'cisco_ios'

            connect_dict = {'device_type': device_type, 'ip': ip, 'username': username, 'password': password}
            print("Connecting to {}....".format(ip))
            try: 
                net_connect = ConnectHandler(**connect_dict)                    
            except NetMikoTimeoutException:
                timeouts.append(ip)
                print("\nSSH session timed trying to connect to the device: {}\n".format(ip))
                continue
            except NetMikoAuthenticationException:
                authfailed.append(ip)
                print("\nSSH authentication failed for device: {}\n".format(ip))
                continue
            except ConnectionRefusedError:
                connectrefused.append(ip)
                print("\nConnection refused for device: {}\n".format(ip))
                continue
            except KeyboardInterrupt:
                print("\nUser interupted connection, closing program.\n")
                sys.exit(0)
            except Exception:
                unknownerror.append(ip)
                print("\nUnknown error connecting to device: {}\n".format(ip))
                continue

            net_connect.enable()
            filename = net_connect.find_prompt().rstrip('#')
            
            filename = filename + '--' + \
            str(datetime.now().year) + '-' + \
            str(datetime.now().month) + '-' + \
            str(datetime.now().day) + '--' + \
            str(datetime.now().hour) + '-' + \
            str(datetime.now().minute) + '-' + \
            str(datetime.now().second) + '.log'
            
            successes.append( (ip , filename) )
            print("Success!")

            output = net_connect.send_command("show ip ospf database")

            if device_type == 'cisco_nxos':
                re_table = jtextfsm.TextFSM(open("cisco_nxos_show_ip_ospf_database.textfsm"))
            re_table = jtextfsm.TextFSM(open("cisco_ios_show_ip_ospf_database.textfsm"))
            fsm_results = re_table.ParseText(output)
            ospf_output = format_fsm_output(re_table, fsm_results)

            with open('output/' + filename, "w") as fout:
                fout.write(output)
                fout.write("\n\n\n")
                for diff in list(dictdiffer.diff(master_ospf, ospf_output)):
                    fout.write(str(diff) + '\n')

    output2()
    print("Finished.\n")

def main():

    if len(sys.argv) != 3:
        print("\nplease provide the following arguments:")
        print("\tpython3 compare-ospf.py <device-list-file> <username>\n\n")
        sys.exit(0)

    device_list = ly(sys.argv[1])
    username = sys.argv[2]
    password = getpass.getpass("Enter Password: ")


    connect(device_list,username,password)


if __name__ == "__main__":
    main()