"""
Description: 
    PA Gratuitous ARP Script
    Connect to PA or Panorama and determine which IP Addresses and Interfaces should
    Send Gratuitous ARP out, typically during the cutover of a new FW.

Requires:
    ipcalc
    requests
    xmltodict
    lxml
    json
        to install try: pip3 install xmltodict requests lxml json ipcalc

Author:
    Ryan Gillespie rgillespie@compunet.biz
    Docstring stolen from Devin Callaway

Tested:
    Tested on macos 10.13.6
    Python: 3.6.2
    PA VM100, Panorama, PA 5250

Example usage:
        $ python3 garp.py <destination folder> <PA(N) mgmt IP> <username>
        Password: 

Cautions:
    - Set DEBUG=True if errors occur and you would like detailed information.
    - Not fully developed.
    

Legal:
    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
    WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
    MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
    ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
    WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
    ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
    OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
"""

import getpass
import sys
import os
import json
import ipcalc

from lxml import etree
import xmltodict
import xml_api_lib_pa as xmlpa

# fmt: off
# Global Variables, debug & xpath location for each profile type
# ENTRY = + "/entry[@name='alert-only']"

class mem: 
    DEBUG = False

    XPATH_ADDRESS_OBJ =  "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/address/entry[@name='ENTRY_NAME']"
    XPATH_ADDRESS_OBJ_PAN = "/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='DEVICE_GROUP']/address/entry[@name='ENTRY_NAME']"

    XPATH_INTERFACES =    "/config/devices/entry[@name='localhost.localdomain']/network/interface"
    XPATH_INTERFACES_PAN =    "/config/devices/entry[@name='localhost.localdomain']/template/entry[@name='TEMPLATE_NAME']/config/devices/entry[@name='localhost.localdomain']/network/interface"

    REST_NATRULES =     "/restapi/9.0/Policies/NATRules?location=vsys&vsys=vsys1"
    REST_NATRULES_PAN = "/restapi/9.0/Policies/NATPostRules?location=device-group&device-group=DEVICE_GROUP"
    
    ip_to_eth_dict = {}
    pa_ip = None
    username = None
    password = None
    fwconn = None
    device_group = None
    root_folder = '.'

# PAN_XML_NATRULES =      "/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='DEVICE_GROUP']/post-rulebase/nat/rules"

# fmt: on

# Used to find the translated addresses
def iterdict(d, searchfor):
    for k, v in d.items():
        if searchfor in k:
            return v
        elif isinstance(v, dict):
            if not v:
                print(f"system error..\nk={k}\nv={v}")
                sys.exit(0)
            return iterdict(v, searchfor)
        else:
            pass


def interface_lookup(ip):
    for key, v in mem.ip_to_eth_dict.items():
        iprange = ipcalc.Network(key)
        if ip in iprange:
            return v


def address_lookup(entry):

    if mem.pa_or_pan == "panorama":
        XPATH = mem.XPATH_ADDRESS_OBJ_PAN.replace("DEVICE_GROUP", mem.device_group)
        XPATH = XPATH.replace("ENTRY_NAME", entry)
    else:
        XPATH = mem.XPATH_ADDRESS_OBJ.replace("ENTRY_NAME", entry)

    output = mem.fwconn.grab_api_output("xml", XPATH, f"{mem.root_folder}/address.xml")

    # Need to check for no response, must be an IP not address
    if "entry" in output["response"]["result"]:
        ips = output["response"]["result"]["entry"]["ip-netmask"]
    else:
        # It must be an IP/Mask already
        ips = entry

    if ips is list:
        for ip in ips:
            ips.append(ip)
    else:
        ips = [ips]

    return ips


def garp_interfaces(entries, iftype):

    garp_commands = []

    if entries:
        # SEARCH ENTRIES
        print(f"\n\nSearching through {iftype} interfaces")
        for entry in entries["entry"]:

            ifname = entry["@name"]
            garp_command = "test arp gratuitous ip IPADDRESS interface IFNAME"

            if "layer3" in entry:
                if "ip" in entry["layer3"]:
                    if type(entry["layer3"]["ip"]["entry"]) is list:
                        for xip in entry["layer3"]["ip"]["entry"]:
                            ip = xip["@name"]
                            temp = garp_command.replace(
                                "IPADDRESS", ip.split("/", 1)[0]
                            )  # removes anything in IP after /, ie /24
                            temp = temp.replace("IFNAME", ifname)
                            garp_commands.append(temp)
                            mem.ip_to_eth_dict.update({ip: ifname})
                    else:
                        ip = entry["layer3"]["ip"]["entry"]["@name"]
                        temp = garp_command.replace(
                            "IPADDRESS", ip.split("/", 1)[0]
                        )  # removes anything in IP after /, ie /24
                        temp = temp.replace("IFNAME", ifname)
                        garp_commands.append(temp)
                        mem.ip_to_eth_dict.update({ip: ifname})
                elif "units" in entry["layer3"]:
                    # Sub Interfaces
                    if entry["layer3"]["units"]["entry"].__len__() > 1:
                        for subif in entry["layer3"]["units"]["entry"]:
                            ifname = subif["@name"]
                            if type(subif["ip"]["entry"]) is list:
                                # Really, secondary addresses on subinterfaces?!
                                print(
                                    f"FOUND SUBIF WITH SECONDARY IP ADDRESS, {ifname}"
                                )
                                for subif_xip in subif["ip"]["entry"]:
                                    ip = subif_xip["@name"]
                                    temp = garp_command.replace(
                                        "IPADDRESS", ip.split("/", 1)[0]
                                    )  # removes anything in IP after /, ie /24
                                    temp = temp.replace("IFNAME", ifname)
                                    garp_commands.append(temp)
                                    mem.ip_to_eth_dict.update({ip: ifname})
                            else:
                                ip = subif["ip"]["entry"]["@name"]
                                temp = garp_command.replace(
                                    "IPADDRESS", ip.split("/", 1)[0]
                                )  # removes anything in IP after /, ie /24
                                temp = temp.replace("IFNAME", ifname)
                                garp_commands.append(temp)
                                mem.ip_to_eth_dict.update({ip: ifname})
                    else:
                        print("ONLY ONE SUBIF")
                else:
                    garp_commands.append(
                        f"No IP address found (e1)(DHCP?), {entry['@name']}"
                    )
            else:
                garp_commands.append(f"No IP address found (e2), {entry['@name']}")
    else:
        print(f"\nNo interfaces found for '{iftype}' type interfaces\n")

    return garp_commands


def garp_natrules(entries):
    garp_commands = []
    if entries:
        print(f"\n\nSearching through natrules interfaces")
        for entry in entries:
            garp_command = "test arp gratuitous ip IPADDRESS interface IFNAME"
            ip = None

            if "disabled" in entry:
                if entry["disabled"] == "yes":
                    print(f"disabled = {entry['disabled']}")
            if "destination-translation" in entry:
                # print(f"dnat = {entry['destination-translation']}")
                # print("RYAN ADD CHECK FOR INTERFACE-ADDRESS----CATCH A USE CASE.")
                garp_commands.append(
                    f"DNAT, - Check NAT rule named: {entry['@name']} for details."
                )
                # obj = iterdict(entry['destination-translation'])
            if "source-translation" in entry:
                snat = entry["source-translation"]

                # Returns Address Object typically, could also be an IP
                obj = iterdict(snat, "translated-address")

                # Usually 'translated-address' but check for 'interface-address'
                if obj:

                    if isinstance(obj, dict):
                        ipobjs = []
                        [ipobjs.append(o) for o in obj["member"]]

                        for ipobj in ipobjs:

                            ips = address_lookup(ipobj)

                            for ip in ips:
                                ifname = interface_lookup(ip)
                                if not ifname:
                                    ifname = "INTERFACE NOT FOUND"
                                temp = garp_command.replace(
                                    "IPADDRESS", ip.split("/", 1)[0]
                                )  # removes anything in IP after /, ie /24
                                temp = temp.replace("IFNAME", ifname)
                                garp_commands.append(temp)

                    else:
                        # Look up Address Object to get actual value
                        ips = address_lookup(obj)

                        for ip in ips:
                            ifname = interface_lookup(ip)
                            if not ifname:
                                ifname = "INTERFACE NOT FOUND"
                            temp = garp_command.replace(
                                "IPADDRESS", ip.split("/", 1)[0]
                            )  # removes anything in IP after /, ie /24
                            temp = temp.replace("IFNAME", ifname)
                            garp_commands.append(temp)
                else:
                    obj = iterdict(snat, "interface-address")
                    if obj:
                        ifname = snat["dynamic-ip-and-port"]["interface-address"][
                            "interface"
                        ]
                        if "ip" in snat["dynamic-ip-and-port"]["interface-address"]:
                            ipobj = snat["dynamic-ip-and-port"]["interface-address"][
                                "ip"
                            ]
                            ips = address_lookup(ipobj)
                            for ip in ips:
                                temp = garp_command.replace(
                                    "IPADDRESS", ip.split("/", 1)[0]
                                )  # removes anything in IP after /, ie /24
                                temp = temp.replace("IFNAME", ifname)
                                garp_commands.append(temp)
                        else:
                            ip = "IP NOT FOUND, ARP should be taken care of via: "
                            temp = garp_command.replace(
                                "IPADDRESS", ip.split("/", 1)[0]
                            )  # removes anything in IP after /, ie /24
                            temp = temp.replace("IFNAME", ifname)
                            garp_commands.append(temp)
                    else:
                        garp_commands.append(
                            f"Error, SNAT configured without a translated IP (e2), {snat}"
                        )
    else:
        print(f"No nat rules found for 'natrules")

    return garp_commands


def garp_logic(pa_ip, username, password, pa_or_pan, root_folder=None):

    mem.pa_ip = pa_ip
    mem.username = username
    mem.password = password
    mem.fwconn = xmlpa.xml_api_lib_pa(mem.pa_ip, mem.username, mem.password)
    mem.pa_or_pan = pa_or_pan
    mem.root_folder = root_folder

    if mem.pa_or_pan == "panorama":
        # Needs Template Name & Device Group
        template_name = input("\nEnter the Template Name (CORRECTLY!): ")
        mem.device_group = input("\nEnter the Device Group Name (CORRECTLY!): ")

        XPATH_INTERFACES = mem.XPATH_INTERFACES_PAN
        XPATH_INTERFACES = XPATH_INTERFACES.replace("TEMPLATE_NAME", template_name)
        XPATH_INTERFACES = XPATH_INTERFACES.replace("DEVICE_GROUP", mem.device_group)
        REST_NATRULES = mem.REST_NATRULES_PAN
        REST_NATRULES = REST_NATRULES.replace("TEMPLATE_NAME", template_name)
        REST_NATRULES = REST_NATRULES.replace("DEVICE_GROUP", mem.device_group)
    else:
        XPATH_INTERFACES = mem.XPATH_INTERFACES
        REST_NATRULES = mem.REST_NATRULES

    # Grab Interfaces (XML)
    int_output = mem.fwconn.grab_api_output(
        "xml", XPATH_INTERFACES, f"{mem.root_folder}/interfaces.xml"
    )

    # Grab NAT Rules (REST)
    nat_output = mem.fwconn.grab_api_output(
        "rest", REST_NATRULES, f"{mem.root_folder}/natrules.json"
    )

    # INTERFACES
    eth_entries = (
        int_output.get("response").get("result").get("interface").get("ethernet")
    )
    ae_entries = (
        int_output.get("response")
        .get("result")
        .get("interface")
        .get("aggregate-ethernet")
    )

    eth_garp = garp_interfaces(eth_entries, "ethernet")
    ae_garp = garp_interfaces(ae_entries, "aggregate-ethernet")

    garp_commands = eth_garp + ae_garp

    # Going through NAT rules

    print("\nPlease wait..\n")

    nat_entries = nat_output.get("result").get("entry")

    nat_garp = garp_natrules(nat_entries)

    output = garp_commands + nat_garp

    print(f"\ngARP Test Commands:")
    print("-------------------------------------------------------------")
    for line in output:
        print(line)
    print("-------------------------------------------------------------")


# If run from the command line
if __name__ == "__main__":

    # Guidance on how to use the script
    if len(sys.argv) != 4:
        print("\nplease provide the following arguments:")
        print("\tpython3 garp.py <output folder location> <PA mgmt IP> <username>\n\n")
        sys.exit(0)

    # Gather input
    root_folder = sys.argv[1]
    pa_ip = sys.argv[2]
    username = sys.argv[3]
    password = getpass.getpass("Enter Password: ")

    # Create connection with the Palo Alto as 'obj'
    paobj = xmlpa.xml_api_lib_pa(pa_ip, username, password)

    # PA or Panorama?
    allowed = list("12")  # Allowed user input
    incorrect_input = True
    while incorrect_input:
        pa_or_pan = input(
            """\nIs this a PA Firewall or Panorama?

        1) PA (Firewall)
        2) Panorama (PAN)

        Enter 1 or 2: """
        )

        for value in pa_or_pan:
            if value not in allowed:
                incorrect_input = True
                break
            else:
                incorrect_input = False

    if pa_or_pan == "1":
        pa_or_pan = "pa"
    else:
        pa_or_pan = "panorama"

    # Run program
    garp_logic(pa_ip, username, password, pa_or_pan, root_folder)
