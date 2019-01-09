"""
Description: 
    Add VLAN's to a Meraki MX Appliance

Requires:
    nada

Author:
    Ryan Gillespie rgillespie@compunet.biz
    Docstring stolen from Devin Callaway

Tested:
    Tested on macos 10.12.3, Windows 10
    Python: 3.6.2

Example usage:
        $ python3 add_vlans.py <vlan_list_file.yml> <Meraki API Key>

Cautions:
    - Set DEBUG=True if errors occur and you would like detailed information.
    - If you have access to multiple Organizations/Networks..USE CAREFULLY
    

Legal:
    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
    WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
    MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
    ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
    WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
    ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
    OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
"""
import sys
import json
import yaml

import rest_api_lib_meraki as meraki

# Return available organizations
def grab_organizations():
    return obj.get_request("organizations")

# Return available networks
def grab_networks(ORGID):
    return obj.get_request(f"organizations/{ORGID}/networks")

# Load YAML
def ly(filename):
    try:
        with open(filename) as _:
            return yaml.load(_)
    except:
        print("Invalid vlan list file!")
        sys.exit(0)

# Main Program
def main(obj, vlan_list):
    # Grab Organizations
    orgs = grab_organizations()

    # MENU
    correct = False
    while not correct:
        print("\nWhich organization would you like to add VLAN's to?\n")
        for key, org in enumerate(orgs):
            print(str(key) + '\t' + org['name'])
        user_input = input("\nEnter the number to the left of the organzation: ")

        # Ensure user enters proper input
        index = int(user_input)
        if 0 <= index < len(orgs):
            correct = True

    # Set organization variables
    ORGNAME = orgs[index]['name']
    ORGID = orgs[index]['id']

    # Grab Networks
    networks = grab_networks(ORGID)

    # MENU
    correct = False
    while not correct:
        print("\nWhich network in this organization would you like to add VLAN's to?\n")
        for key, net in enumerate(networks):
            print(str(key) + '\t' + net['name'])
        user_input = input("\nEnter the number to the left of the desired network: ")

        # Ensure user enters proper input
        index = int(user_input)
        if 0 <= index < len(orgs):
            correct = True

    # Set network variables
    NETNAME = networks[index]['name']
    NETID = networks[index]['id']

    # Let user double-check before pushing new vlans
    print("\n\n=====================================================\n")
    print("Thank you!")
    print(f"\nThe below VLAN's will be created in:\n")
    print(f"Organization: {ORGNAME}")
    print(f"Network: {NETNAME}\n")
    print("VLAN List:")
    for vlan in VLANS:
        print("ID: " + str(vlan["id"]) + "\tName: " + vlan["name"] + "\tSubnet: " + vlan["subnet"] + "\tMX IP: " + vlan["applianceIp"])
    print("\n=====================================================")

    proceed = False
    while not proceed:
        yesno = input("Proceed? (y/n): ")
        if yesno == 'y':
            proceed = True
        elif yesno == 'n':
            print("\nPlease try again. Exiting...\n")
            sys.exit(0)
        elif yesno not in 'yn':
            continue

    # Push VLAN's to Meraki Organization/Network
    for vlan in VLANS:
        print()
        result = obj.post_request(f"networks/{NETID}/vlans", vlan)
        if result == "Success":
            print(f"Created VLAN: {vlan['id']}")
        else:
            error = json.loads(result.content)
            print(f"Error creating vlan: {vlan['id']}")
            print(f"Status Code: {result.status_code}")
            print(f"Error: {error['errors']}")

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

    # Create/test connection with Meraki as 'obj'
    obj = meraki.rest_api_lib_meraki(APIKEY)

    # Load VLAN's into Python dictionary
    VLANS = ly(vlan_list)

    # Run program
    main(obj, VLANS)

    # Done!
    print("\n\nComplete!\n")
