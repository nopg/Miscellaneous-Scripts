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
        to install try: pip3 install xmltodict requests lxml ipcalc

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
    - Source-NAT only (discovers and outputs others)
    - Panorama Post-NAT rules only (for now)
    

Legal:
    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
    WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
    MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
    ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
    WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
    ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
    OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
"""

from getpass import getpass
import sys
import os
import json
import ipcalc
import time
import concurrent.futures

from lxml import etree
import xmltodict
import api_lib_pa as pa

# fmt: off
# Global Variables, debug & xpath location for each profile type
# ENTRY = + "/entry[@name='alert-only']"

class mem: 

    XPATH_ADDRESS_OBJ =  "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/address/entry[@name='ENTRY_NAME']"
    XPATH_ADDRESS_OBJ_PAN = "/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='DEVICE_GROUP']/address/entry[@name='ENTRY_NAME']"

    XPATH_INTERFACES =    "/config/devices/entry[@name='localhost.localdomain']/network/interface"
    XPATH_INTERFACES_PAN =    "/config/devices/entry[@name='localhost.localdomain']/template/entry[@name='TEMPLATE_NAME']/config/devices/entry[@name='localhost.localdomain']/network/interface"

    XPATH_DEVICE_GROUPS = "/config/devices/entry[@name='localhost.localdomain']/device-group"
    XPATH_TEMPLATE_NAMES = "/config/devices/entry[@name='localhost.localdomain']/template"

    REST_NATRULES =     "/restapi/9.0/Policies/NATRules?location=vsys&vsys=vsys1"
    REST_NATRULES_PAN = "/restapi/9.0/Policies/NATPostRules?location=device-group&device-group=DEVICE_GROUP"
    
    ip_to_eth_dict = {}
    pa_ip = None
    username = None
    password = None
    fwconn = None
    device_group = None
    root_folder = '.'
    garp_commands = []
    review_nats = []

# PAN_XML_NATRULES =      "/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='DEVICE_GROUP']/post-rulebase/nat/rules"

# fmt: on


def iterdict(d, searchfor):
    """
    Traverse through the dictionary (d) and find the key: (searchfor).
    Return the value of that key.
    """
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
    """
    Used to find which physical interface is associated with this IP (NAT entry).
    Uses existing dictionary mapping ip/mask to physical interface.
    Searches based on the subnet mask in use on the physical interface.
    """
    for key, v in mem.ip_to_eth_dict.items():
        iprange = ipcalc.Network(key)
        if ip in iprange:
            return v


def address_lookup(entry):
    """
    Used to find the translated addresses objects on the PA/Panorama.
    Runs another api call to grab the object and return it's value (the actual ip address)
    If the NAT rule isn't using an object, we can assume this value is the IP address.
    Returns a LIST
    """
    if mem.pa_or_pan == "panorama":
        XPATH = mem.XPATH_ADDRESS_OBJ_PAN.replace("DEVICE_GROUP", mem.device_group)
        XPATH = XPATH.replace("ENTRY_NAME", entry)
    else:
        XPATH = mem.XPATH_ADDRESS_OBJ.replace("ENTRY_NAME", entry)

    filename = entry.split("/", 1)[0]
    output = mem.fwconn.grab_api_output("xml", XPATH, f"{mem.root_folder}/address-obj--{filename}.xml")

    # Need to check for no response, must be an IP not address
    if "entry" in output["response"]["result"]:
        if "ip-netmask" in output["response"]["result"]["entry"]:
            ips = output["response"]["result"]["entry"]["ip-netmask"]
        else:
            add_review_entry(output["response"]["result"]["entry"], "not-ip-netmask")
    else:
        # It must be an IP/Mask already
        ips = entry

    if ips is list:
        for ip in ips:
            ips.append(ip)
    else:
        ips = [ips]

    return ips


def grab_panorama_objects():
    temp_device_groups = mem.fwconn.grab_api_output("xml", mem.XPATH_DEVICE_GROUPS, f"{mem.root_folder}/device_groups.xml")
    temp_template_names = mem.fwconn.grab_api_output("xml", mem.XPATH_TEMPLATE_NAMES, f"{mem.root_folder}/template_names.xml")
    device_groups = []
    template_names = []

    # Need to check for no response, must be an IP not address
    if "entry" in temp_device_groups["response"]["result"]["device-group"]:
        for entry in temp_device_groups["response"]["result"]["device-group"]["entry"]:
            device_groups.append(entry["@name"])
    else:
        print(f"Error, Panorama chosen but no Device Groups found.")
        sys.exit(0)

   # Need to check for no response, must be an IP not address
    if "entry" in temp_template_names["response"]["result"]["template"]:
        if isinstance(temp_template_names["response"]["result"]["template"]["entry"],list):
            for entry in temp_template_names["response"]["result"]["template"]["entry"]:
                template_names.append(entry["@name"])
        else:
            template_names.append(temp_template_names["response"]["result"]["template"]["entry"]["@name"])
    else:
        print(f"Error, Panorama chosen but no Template Names found.")
        sys.exit(0)
    
    return device_groups, template_names


def add_review_entry(entry, type):
    if type == "disabled":
        mem.review_nats.append(f"Disabled Rule: Check {entry['@name']}")
    elif type == "dnat":
        mem.review_nats.append(f"DNAT, - Check NAT rule named: '{entry['@name']}' for details.")
    elif type == "not-ip-netmask":
        mem.review_nats.append(f"non IP-NETMASK used for translated address: '{entry['@name']}' for details.")

        print("Not implemented yet. Ask Ryan. Send him natrules.json")
        print("Most likely an address-object using 'IP Range', 'IP Wildcard Mask', or 'FQDN'.")
        print("For NAT? I know a couple use cases, but maybe manually add this gARP after reviewing.")
        print("May be redundant or otherwise unnecessary.")

    mem.fwconn.create_json_files(entry, f"{mem.root_folder}/review-{entry['@name']}.xml")


def add_garp_command(ip, ifname):
    """
    Update global garp_commands list.
    First remove the subnet mask from the 'ip' received.
    example: 'test arp gratuitous ip 5.5.5.4 interface ethernet1/1'
    """
    ip = ip.split("/", 1)[0]  # removes anything in IP after /, ie /24
    garp_command = f"test arp gratuitous ip {ip} interface {ifname}"
    return garp_command



def process_interface_entries(entry):
    # Set interface name
    ifname = entry["@name"]
    # Should have an IP
    if "layer3" in entry:
        # Normal IP Address on interface
        if "ip" in entry["layer3"]:
            # Secondary IP Addresses
            if type(entry["layer3"]["ip"]["entry"]) is list:
                commands = []
                for xip in entry["layer3"]["ip"]["entry"]:
                    ip = xip["@name"]
                    mem.ip_to_eth_dict.update({ip: ifname})
                    commands.append(add_garp_command(ip, ifname))
                return commands
            else:  # Normal 1 IP on 1 interface
                ip = entry["layer3"]["ip"]["entry"]["@name"]
                mem.ip_to_eth_dict.update({ip: ifname})
                return add_garp_command(ip, ifname)
        # Sub Interfaces
        elif "units" in entry["layer3"]:
            # Sub Interfaces
            if entry["layer3"]["units"]["entry"].__len__() > 1:
                commands = []
                for subif in entry["layer3"]["units"]["entry"]:
                    # Set new (sub)interface name
                    ifname = subif["@name"]
                    # Secondary IP Addresses
                    if type(subif["ip"]["entry"]) is list:
                        for subif_xip in subif["ip"]["entry"]:
                            ip = subif_xip["@name"]
                            mem.ip_to_eth_dict.update({ip: ifname})
                            commands.append(add_garp_command(ip, ifname))
                    else:  # Normal 1 IP on Subinterface
                        ip = subif["ip"]["entry"]["@name"]
                        mem.ip_to_eth_dict.update({ip: ifname})
                        commands.append(add_garp_command(ip, ifname))
                return commands
            else:  # Can remove this if/else?
                print("ONLY ONE SUBIF")
        else:  # Probably DHCP, should be added
            error = (
                f"No IP address found (e1)(DHCP?), {entry['@name']}"
            )
            return error
    else:  # No 'layer3', no IP Address here.
        error = f"No IP address found (e2), {entry['@name']}"
        return error


def build_garp_interfaces(entries, iftype):
    """
    Search through ethernet and aggregate-ethernet interfaces.
    Build a list of 'test arp' commands based on what is found.
    Return this list.
    """
    results = None
    if entries:
        print(f"\nSearching through {iftype} interfaces")

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(process_interface_entries, entries["entry"])
        
        return results
        
    else:  # No interfaces
        print(f"\nNo interfaces found for '{iftype}' type interfaces\n")


def process_nat_entries(entry):
    ip = None
    if "disabled" in entry:
        if entry["disabled"] == "yes":
            add_review_entry(entry, "disabled")
            return None
    if "destination-translation" in entry:
        add_review_entry(entry, "dnat")
    if "source-translation" in entry:
        snat = entry["source-translation"]

        # Returns Address Object typically, could also be an IP
        # Usually 'translated-address' but also check for 'interface-address'
        addr_obj = iterdict(snat, "translated-address")
        if addr_obj:
            # If it's a dictionary, we have multiple IP's
            if isinstance(addr_obj, dict):
                ipobjs = []
                [ipobjs.append(o) for o in addr_obj["member"]]
                # Find the real-ip from the address object
                for ipobj in ipobjs:
                    ips = address_lookup(ipobj)
                    commands = []
                    for ip in ips:
                        ifname = interface_lookup(ip)
                        if not ifname:
                            ifname = "INTERFACE NOT FOUND"
                        commands.append(add_garp_command(ip, ifname))
                    return commands
            else:
                # Find the real-ip from the address object
                ips = address_lookup(addr_obj)
                commands = []
                for ip in ips:
                    ifname = interface_lookup(ip)
                    if not ifname:
                        ifname = "INTERFACE NOT FOUND"
                    commands.append(add_garp_command(ip, ifname))
                return commands
        else:
            # Checking for interface-address?
            addr_obj = iterdict(snat, "interface-address")
            if addr_obj:
                ifname = snat["dynamic-ip-and-port"]["interface-address"][
                    "interface"
                ]
                if "ip" in snat["dynamic-ip-and-port"]["interface-address"]:
                    ipobj = snat["dynamic-ip-and-port"]["interface-address"][
                        "ip"
                    ]
                    ips = address_lookup(ipobj)
                    for ip in ips:
                        return add_garp_command(ip, ifname)
                else:  # No IP found(DHCP?), since we have interface should already have a 'test' command for it
                    ip = "IP NOT FOUND, ARP taken care of via: "
                    return add_garp_command(ip, ifname)
            else:  # SNAT Misconfigured
                error =  (
                    f"Error, SNAT configured without a translated IP (e2), {snat}"
                )
                return error
    
    return None


def build_garp_natrules(entries):
    """
    Search through PA/Panorama NAT Rules.
    Build a list of 'test arp' commands based on what is found.
    Currently only supports source-nat, and post-nat (panorama) rules.
    Return this list.
    """
    results = None
    if entries:
        print(f"\nSearching through natrules interfaces")
        print("\nPlease wait..\n")

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(process_nat_entries, entries)
        
        return results

    else:  # No Natrules
        print(f"No nat rules found for 'natrules")
        return []
    


def garp_logic(pa_ip, username, password, pa_or_pan, root_folder=None):
    """
    Main point of entry.
    Connect to PA/Panorama.
    Grab 'test arp' output from interfaces and NAT rules.
    Print out the commands.
    """
    mem.pa_ip = pa_ip
    mem.username = username
    mem.password = password
    mem.fwconn = pa.api_lib_pa(mem.pa_ip, mem.username, mem.password)
    mem.pa_or_pan = pa_or_pan
    mem.root_folder = root_folder

    # Set the correct XPATH for what we need (interfaces and nat rules)
    if mem.pa_or_pan == "panorama":

        # Needs Template Name & Device Group
        device_groups, template_names = grab_panorama_objects()
        print("\nTemplate Names:")
        print("---------------------")
        for template in template_names:
            print(template)
        print("--------------\n")
        print("Device Groups:")
        print("--------------")
        for dg in device_groups:
            print(dg)
            
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

    start = time.perf_counter()
    
    # Grab Interfaces (XML)
    int_output = mem.fwconn.grab_api_output(
        "xml", XPATH_INTERFACES, f"{mem.root_folder}/interfaces.xml"
    )

    # Grab NAT Rules (REST, 9.0+)
    nat_output = mem.fwconn.grab_api_output(
        "rest", REST_NATRULES, f"{mem.root_folder}/natrules.json"
   )

    if int_output["response"]["result"]["@count"] == "0":
        print("\nNo interfaces found, check interfaces.xml for API Reply\n")
        sys.exit(0)
    
    if nat_output["result"]["@count"] == "0":
        print("\nNo NAT Rules found, check natrules.xml for API Reply\n")
        sys.exit(0)

    # Parse XML to get to what we need closer to a dictionary
    eth_entries = (
        int_output.get("response").get("result").get("interface").get("ethernet")
    )
    ae_entries = (
        int_output.get("response")
        .get("result")
        .get("interface")
        .get("aggregate-ethernet")
    )
    nat_entries = nat_output.get("result").get("entry")

    # Interfaces
    mem.garp_commands.append(
        "--------------------ARP FOR Interfaces---------------------"
    )

    eth_commands = build_garp_interfaces(eth_entries, "ethernet")
    ae_commands = build_garp_interfaces(ae_entries, "aggregate-ethernet")

    if eth_commands:
        for command in eth_commands:
            if isinstance(command,list):
                for ip in command:
                    mem.garp_commands.append(ip)
            else:
                mem.garp_commands.append(command)
    if ae_commands:
        for command in ae_commands:
            if isinstance(command,list):
                for ip in command:
                    mem.garp_commands.append(ip)        
            else:
                mem.garp_commands.append(command)

    # NAT Rules
    mem.garp_commands.append(
        "-------------------------ARP FOR NAT-----------------------"
    )
    garp_nat_commands = build_garp_natrules(nat_entries)
    for command in garp_nat_commands:
        if command:
            mem.garp_commands.append(command)


    # Print out all the commands/output!
    print(f"\ngARP Test Commands:")
    print("-----------------------------------------------------------")
    for line in mem.garp_commands:
        print(line)
    print("-----------------------------------------------------------")

    print("--------------------REVIEW THESE NATS----------------------")
    for nat in mem.review_nats:
        print(nat)
    print("-----------------------------------------------------------\n")
    end = time.perf_counter()
    runtime = end - start
    print(f"Took {runtime} Seconds.")



# If run from the command line
if __name__ == "__main__":

    root_folder = None
    # Guidance on how to use the script
    if len(sys.argv) == 4:
        root_folder = sys.argv[3]
    elif len(sys.argv) != 3:
        print("\nplease provide the following arguments:")
        print(
            "\tpython3 garp.py <PA/Panorama IP> <username> <optional output folder>\n\n"
        )
        sys.exit(0)

    if not root_folder:
        root_folder = "~temp/"

    # Gather input
    pa_ip = sys.argv[1]
    username = sys.argv[2]
    password = getpass("Enter Password: ")

    # Create connection with the Palo Alto as 'obj' to test login success
    try:
        paobj = pa.api_lib_pa(pa_ip, username, password)
    except:
        print(f"Error connecting to: {pa_ip}\nCheck username/password and network connectivity.")
        sys.exit(0)

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
