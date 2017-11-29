from datetime import datetime
import sys
import yaml
from netmiko import ConnectHandler
from netmiko.ssh_exception import *

def ly(filename):
    with open(filename) as _:
        return yaml.load(_)

def gather_configs(fin,configpath,username,password,COMMANDS):
    start_time = datetime.now()
    devices = ly(fin)
    timeouts = []
    authfailed = []
    connectrefused = []
    unknownerror = []
    successes = []
    print("\n\n\nThank you! Gathering Output..\n\n\n")

    for type in devices:
        for device in devices[type]:
            if type == 'IOS':
                device_type = 'cisco_ios'
                ip = device
            elif type == 'NX-OS':
                device_type = 'cisco_nxos'
                ip = device                
            elif type == 'ASA':
                device_type = 'cisco_asa'
                ip = device                
            elif type == 'TELNET':
                device_type = 'cisco_ios_telnet'
                ip = device[0]
                telnetpassword = device[1]
                enablepass = device[2]

            if(type == 'TELNET'):
                connect_dict = {'device_type': device_type, 'ip': ip, 'username': username, 'password': telnetpassword, 'secret': enablepass}
            else:
                connect_dict = {'device_type': device_type, 'ip': ip, 'username': username, 'password': password}

            print(f"Connecting to {ip}.....", end='', flush=True)
            try: 
                net_connect = ConnectHandler(**connect_dict)
                if(type == 'TELNET'):
                    net_connect.enable()
                    
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

            output = net_connect.send_command("show run | inc hostname")
            if not output:
                filename = net_connect.send_command("show hostname").strip()
            else:
                filename = output[9:]

            filename = filename + '-' + \
            str(datetime.now().year) + '-' + \
            str(datetime.now().month) + '-' + \
            str(datetime.now().day) + '--' + \
            str(datetime.now().hour) + '-' + \
            str(datetime.now().minute) + '-' + \
            str(datetime.now().second) + '.log'
            
            successes.append( (ip , filename + ".log") )
            print("Success!", flush=True)
            
            if configpath == '':
                output = net_connect.send_config_set(COMMANDS)
                print(output)
            else:
                try:
                    with open(configpath + "/" + filename,'w') as fout:
                        for command in COMMANDS:
                            print("Running Command: {}\n".format(command), flush=True)
                            fout.write('\n\nRunning Command:\n' + command + '\n\n')
                            output = net_connect.send_command(command)
                            print(output)
                            fout.write(output)
                except:
                    print("Invalid destination folder!")
                    output = net_connect.send_config_set(COMMANDS)
                    print(output)
    
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

    return