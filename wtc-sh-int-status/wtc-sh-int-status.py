"""
Built for Warner Truck Center 6500 Migration
"""
import sys
import jtextfsm
import csv
from netmiko import ConnectHandler
from netmiko.ssh_exception import *



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

    # execute the show cdp neighbor detail command
    # we increase the delay_factor for this command, because it take some time if many devices are seen by CDP
    result = ssh_connection.send_command("show interface status", delay_factor=2)

    # close SSH connection
    ssh_connection.disconnect()

    return result

def format_fsm_output(re_table, fsm_results):
    #   FORMAT FSM OUTPUT(LIST OF LIST) INTO PYTHON LIST OF DICTIONARY VALUES BASED ON TEMPLATE #
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

def build_csv(output):

    fout = open('int-status-output.csv', 'w')

    writer = csv.DictWriter(fout, fieldnames=re_table.header, lineterminator='\n')
    writer.writeheader()
    writer.writerows(output)

    fout.close()

def main(ip, username, password):

    int_status = get_show_int_status(ip, username, password)

    if int_status in ("TIMEOUT", "AUTHFAIL", "CONNECTREFUSED", "UNKNOWN"):
        print(int_status)
        sys.exit(0)

    # parse the show cdp details command using TextFSM
    re_table = jtextfsm.TextFSM(open("cisco_ios_show_interfaces_status.textfsm"))
    fsm_results = re_table.ParseText(int_status)

    ## REFORMAT THE OUTPUT ##
    output = format_fsm_output(re_table, fsm_results)

    build_csv(output)


if __name__ == "__main__":

    if len(sys.argv) != 3:
        print("\nplease provide the following arguments:")
        print("\tcollect-cdp-information.py <ip> <username>\n\n")
        sys.exit(0)

    target_ip = sys.argv[1]
    username = sys.argv[2]
    password = input("Type the password: ")

    main(target_ip, username, password)
    print("Done.")