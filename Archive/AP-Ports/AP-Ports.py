import jtextfsm
import yaml
from netmiko import ConnectHandler
from netmiko.ssh_exception import *

def ly(filename):
    with open(filename) as _:
        return yaml.load(_)

username = input("Username: ")
password = input("Password: ")
switchfile = input("Name of hosts file (list of switch IP's) including extension: ")
searchstring = input("String or model to search for in CDP output (i.e. \'AIR-\' for Access Points): ")

#   OPEN INPUT/OUTPUT FILES #
devices = ly(switchfile)
with open("./output.log", 'w') as fout:

#   GRAB CDP NEIGHBORS #
    for ip in devices:
        connect_dict = {'device_type': 'cisco_ios', 'ip': ip, 'username': username, 'password': password}

        fout.write("\nSwitch: {}\n".format(ip))
        fout.write("------------------------\n")

        try:
            net_connect = ConnectHandler(**connect_dict)
        except NetMikoTimeoutException:
            fout.write("\nUnable to connect (timeout) !\n\n\n\n")
            continue
        except NetMikoAuthenticationException:
            fout.write("\nUnable to connect (authentication failure) !\n\n\n\n")
            continue

        output = net_connect.send_command("show cdp neighbor detail")
        
        template = open("cisco_ios_show_cdp_neighbors_detail.template")
        re_table = jtextfsm.TextFSM(template)
        fsm_results = re_table.ParseText(output)
    
#   FORMAT NEIGHBORS OUTPUT(LIST OF LIST) INTO PYTHON LIST OF DICTIONARY VALUES (neighbor, port, ip address, etc) #
        cdpneighbors = []
        for neighbor in fsm_results:
            tempdevice = {}
            for position, header in enumerate(re_table.header):
                tempdevice[header] = neighbor[position]
            cdpneighbors.append(tempdevice)
    
#   SEARCH FOR DEVICES AND PRINT/SAVE OUTPUT #
        found = 0
        for device in cdpneighbors:
            if searchstring in device['PLATFORM']:
                found += 1
                fout.write("\nConnected device: {} found on port: {}\n".format(device['DESTINATION_HOST'], device['LOCAL_PORT']))
                fout.write(net_connect.send_command("show run interface {}".format(device['LOCAL_PORT'])))
        fout.write("\nFound {} devices matching \'{}\'\n\n\n\n".format(found, searchstring))

fout.close()
print("\nFinished, output located in \'output.log\' file\n")
