import sys
from getpass import getpass
import json
import logging

import rest_api_lib_meraki as meraki
from scrapli import Scrapli
from scrapli.helper import textfsm_parse
#from scrapli.driver.core import IOSXEDriver


#logging.basicConfig(filename="scrapli.log", level=logging.DEBUG)

# Main Program
def main(mydashboard):

    orgid = input("Org ID: ")
    serial = input("Serial: ")
    # MERAKI BASICS WORKING
    ################################
    # # Grab Organizations
    # orgs = mydashboard.get_organizations()

    # print(f"Orgs = \n\n {orgs}")

    # # Grab Networks
    # networks = mydashboard.get_networks(int(orgid))

    # print(f"Networks = \n\n {networks}")

    # # Grab Switch port status
    # statuses = mydashboard.get_switch_ports_status(serial)

    # print(f"Statuses = \n\n {statuses}")

    # # Grab Switch port status
    # portconfig = mydashboard.get_switch_ports_config(serial)
    # port2config = mydashboard.get_switch_ports_config(serial, "2")

    # print(f"\n\nPorts config = \n\n {portconfig}")
    # print(f"\n\nPort 2 config = \n\n {port2config}")

    # SCRAPLI BASICS JUST STARTING
    ################################

    auth_password = getpass("Password: ")

    MY_DEVICE = {
        "host": "10.254.254.1",
        "auth_username": "admin",
        "auth_password": auth_password,
        "auth_strict_key": False,
        "platform": "cisco_iosxe",
        "transport_options": {"open_cmd": ["-c", "aes128-cbc"]},
    }

    with Scrapli(**MY_DEVICE) as conn:
    #with IOSXEDriver(**MY_DEVICE) as conn:
    #    response = conn.send_command("show version")
        print(conn.get_prompt())
        test = conn.send_command("show ip interface brief")
        print(test.textfsm_parse_output())
        print(f"\n\n{test.channel_input}")

        commands = ["show version", "show ip bgp summary"]
        test2 = conn.send_commands(commands)
        print(dir(test2))
        print(test2.result)
        print("\n\nhi\n\n")
        print(test2)
        for i in test2:
            print(i)
        print(test2[0].result)

        test3 = conn.send_command("show interfaces status")
        
        structured_result = textfsm_parse("cisco_ios_show_interfaces_status_physical_only.textfsm", test3.result)
        print(structured_result)
        print("\n\nhere we go\n\n")
        print(test3.textfsm_parse_output())

        # Create to compare
        with open("customtextfsm.json", 'w') as fout:
            fout.write(json.dumps(structured_result, indent=4))

        with open("ntctextfsm.json", 'w') as fout:
            fout.write(json.dumps(test3.textfsm_parse_output(), indent=4))

        structured_result = test3.genie_parse_output()
        with open("genietextfsm.json", 'w') as fout:
            fout.write(json.dumps(structured_result, indent=4))

    #print(response.result)


# If run from the command line
if __name__ == "__main__":
    # Guidance on how to use the script
    if len(sys.argv) != 3:
        print("\nplease provide the following arguments:")
        print(
            "\tpython3 add_vlans.py <vlan_list_file.yml> <Meraki API Key>\n\n"
        )
        sys.exit(0)

    # Gather input
    vlan_list = sys.argv[1]
    APIKEY = sys.argv[2]

    # Create/test connection with Meraki as 'mydashboard'
    mydashboard = meraki.rest_api_lib_meraki(APIKEY)
    
    # Run program
    main(mydashboard)

    # Done!
    print("\n\nComplete!\n")