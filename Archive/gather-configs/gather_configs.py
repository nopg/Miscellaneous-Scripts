from datetime import datetime

import yaml
from netmiko import ConnectHandler
from netmiko.ssh_exception import *

def ly(filename):
    with open(filename) as _:
        return yaml.load(_)

def gather_configs(fin,configpath,username,password):
    start_time = datetime.now()
    devices = ly(fin)
    timeouts = []
    skipped = []
    successes = []
    except_timeout = False
    except_auth = False
    new_ip = '1'
    new_username = '1'
    print("\n\n\nThank you! Gathering Configs...\n\n\n")
    
    for ip in devices:
        net_connect = None
        while net_connect == None:
            try:
                if except_timeout:
                    connect_dict = {'device_type': 'cisco_ios', 'ip': new_ip, 'username': username, 'password': password}
                    except_timeout = False
                elif except_auth:
                    connect_dict = {'device_type': 'cisco_ios', 'ip': ip, 'username': new_username, 'password': new_password}
                    except_auth = False
                else:
                    connect_dict = {'device_type': 'cisco_ios', 'ip': ip, 'username': username, 'password': password}
                    
                net_connect = ConnectHandler(**connect_dict)
            except NetMikoTimeoutException:
                if except_timeout:
                    old_ip = new_ip
                else:
                    old_ip = ip
                except_timeout = True
                timeouts.append(old_ip)
                print("\nSSH session timed trying to connect to the device: {}\n".format(old_ip))
                new_ip = input("Please enter a new IP address or '0' to skip: ")
                if new_ip == '0':
                    skipped.append(old_ip)
                    except_timeout = False
                    break 
            except NetMikoAuthenticationException:
                if except_timeout:
                    old_ip = new_ip
                else:
                    old_ip = ip
                except_auth = True
                print("\nSSH authentication failed for device: {}\n".format(old_ip))
                new_username = input("Please enter the username or '0' to skip: ")
                if new_username == '0':
                    skipped.append(old_ip)
                    except_auth = False
                    break
                new_password = input("Enter the password: ")
    
        if new_ip == '0' or new_username == '0':
            continue
        
        output = net_connect.send_command("show run | inc hostname")
        filename = output[9:]
        successes.append( (ip , filename + ".cfg") )
        with open(configpath + "\\" + filename + ".cfg",'w') as fout:
            fout.write(net_connect.send_command("show run"))
            fout.write("\n\n\n")
            fout.write(net_connect.send_command("show version"))
            
        #net_connect.disconnect()
    
    print("\n\n\n\n\n\n")
    print("Devices timed out: ")
    for each in timeouts:
        print(each)
    print()
    print("Skipped devices: ")
    for each in skipped:
        print(each)
    print()
    print("Successful: ")
    for addr,fname in successes:
        print("{:15s} {:15s}".format(addr,fname))
    print()
    print("Time elapsed: {}".format(datetime.now() - start_time))
