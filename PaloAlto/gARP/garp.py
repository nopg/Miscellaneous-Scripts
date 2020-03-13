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
DEBUG = False

XPATH_ADDRESS_OBJ =  "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/address/entry[@name='ENTRY_NAME']"
XPATH_ADDRESS_OBJ_PAN = "/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='DEVICE_GROUP']/address/entry[@name='ENTRY_NAME']"

XPATH_INTERFACES =    "/config/devices/entry[@name='localhost.localdomain']/network/interface"
XPATH_INTERFACES_PAN =    "/config/devices/entry[@name='localhost.localdomain']/template/entry[@name='TEMPLATE_NAME']/config/devices/entry[@name='localhost.localdomain']/network/interface"

REST_NATRULES =     "/restapi/9.0/Policies/NATRules?location=vsys&vsys=vsys1"
REST_NATRULES_PAN = "/restapi/9.0/Policies/NATPostRules?location=device-group&device-group=DEVICE_GROUP"


#PAN_XML_NATRULES =      "/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='DEVICE_GROUP']/post-rulebase/nat/rules"

# fmt: on


def grab_api_output(root_folder, xml_or_rest, xpath_or_restcall, outputrequested, obj):
    # Grab PA/Panorama API Output
    success = False
    if xml_or_rest == "xml":
        filename = f"{root_folder}/{outputrequested}.xml"
        response = obj.get_xml_request_pa(
            call_type="config", action="get", xpath=xpath_or_restcall
        )
        xml_response = xmltodict.parse(response)
        if xml_response["response"]["@status"] == "success":
            success = True
        create_xml_files(xml_response, filename)
        if not xml_response["response"]["result"]:
            print(
                "Nothing found on PA/Panorama, are you connecting to the right device? Check output for XML API reply"
            )
            sys.exit(0)

    elif xml_or_rest == "rest":
        filename = f"{root_folder}/{outputrequested}.json"
        response = obj.get_rest_request_pa(restcall=xpath_or_restcall)
        json_response = json.loads(response)
        if json_response["@status"] == "success":
            success = True
        create_json_files(response, filename)
        if not json_response["result"]:
            print(
                "Nothing found on PA/Panorama, are you connecting to the right device? Check output for REST API reply"
            )

    if not success:
        # Extra logging when debugging
        if DEBUG:
            print(f"\nGET request sent: xpath={xpath_or_restcall}.\n")
            print(f"\nResponse: \n{response}")
            create_xml_files(result, filename)
            print(f"Output also written to {filename}")
        else:
            print(f"\nError exporting '{outputrequested}' object.")
            print(
                "(Normally this just means no object found, set DEBUG=True if needed)"
            )
            
    if xml_or_rest == "xml":
        return xml_response
    else:
        return json_response


# Read all .xml files found in folder_name, return list containing all the output
def grab_files(folder_name):
    file_list = []
    for root, dirs, files in os.walk(folder_name):
        for file in files:
            #if file.endswith(".xml"):
            with open(root + "/" + file, "r") as fin:
                data = fin.read()
                file_list.append(data)
    return file_list


# Create file for each profile type
def create_xml_files(temp, filename):

    # Pull folder name from string
    end = filename.rfind("/")
    folder = filename[0:end]

    # Create the root folder and subfolder if it doesn't already exist
    os.makedirs(folder, exist_ok=True)

    # Because XML: remove <response/><result/> and <?xml> tags
    # Using get().get() won't cause exception on KeyError
    # Check for various response type and ensure xml is written consistently
    data = temp.get("response")
    if data:
        # data = temp.get("response").get("result")
        data = {"response": data}
        if data:
            data = xmltodict.unparse(data)
        else:
            data = xmltodict.unparse(temp)
    else:
        data = xmltodict.unparse(temp)
    data = data.replace('<?xml version="1.0" encoding="utf-8"?>', "")

    with open(filename, "w") as fout:
        fout.write(data)


def create_json_files(data, filename):
    """
    CREATE OUTPUT FILES 

    :param data: list of data to be written
    :param template_type: 'feature' or 'device'
    :return: None, print output
    """
    # Pull folder name from string
    end = filename.rfind("/")
    folder = filename[0:end]

    # Create the root folder and subfolder if it doesn't already exist
    os.makedirs(folder, exist_ok=True)
    
    # Write Data
    fout = open(filename, "w")
    fout.write(data)
    fout.close()

    #print("\tCreated: {}\n".format(filename))


# Used to find the translated addresses
def iterdict(d, searchfor):
    for k,v in d.items():
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
    for key, v in ip_to_eth_dict.items():
        iprange = ipcalc.Network(key)
        if ip in iprange:
            return v


def address_lookup(obj, pa_or_pan, device_group, fwconn):
    
    if pa_or_pan == "panorama":
        XPATH = XPATH_ADDRESS_OBJ_PAN.replace("DEVICE_GROUP", device_group)
        XPATH = XPATH.replace("ENTRY_NAME", obj)
    else:
        XPATH = XPATH_ADDRESS_OBJ.replace("ENTRY_NAME", obj)

    output = grab_api_output(".", "xml", XPATH, "address", fwconn)

    # Need to check for no response, must be an IP not address
    if "entry" in output["response"]["result"]:
        ips = output["response"]["result"]["entry"]["ip-netmask"]
    else:
        # Must be an IP/Mask already
        ips = obj
    
    if ips is list:
        for ip in ips:
            ips.append(ip)
    else:
        ips = [ips]
    
    return ips


def garp_interfaces(entries, iftype):

    global ip_to_eth_dict
    garp_commands = []

    if entries:
        # SEARCH ENTRIES
        print(f"\n\nSearching through {iftype} interfaces")
        for entry in entries["entry"]:

            ifname = entry['@name']
            garp_command = "test arp gratuitous ip IPADDRESS interface IFNAME"
            XIPS = False
            SUBIF_XIP = False

            if "layer3" in entry:
                if "ip" in entry["layer3"]:
                    if type(entry['layer3']['ip']['entry']) is list:
                        XIPS = True
                        for xip in entry['layer3']['ip']['entry']:
                            ip = xip['@name']
                            temp = garp_command.replace('IPADDRESS', ip.split('/',1)[0]) # removes anything in IP after /, ie /24
                            temp = temp.replace('IFNAME', ifname)
                            garp_commands.append(temp)
                            ip_to_eth_dict.update({ip:ifname})
                    else: 
                        ip = entry['layer3']['ip']['entry']['@name']
                        temp = garp_command.replace('IPADDRESS', ip.split('/',1)[0]) # removes anything in IP after /, ie /24
                        temp = temp.replace('IFNAME', ifname)
                        garp_commands.append(temp)
                        ip_to_eth_dict.update({ip:ifname})
                elif "units" in entry["layer3"]:
                    # Sub Interfaces
                    XIPS = True
                    if entry['layer3']['units']['entry'].__len__() > 1:
                        for subif in entry['layer3']['units']['entry']:
                            ifname = subif['@name']
                            if type(subif['ip']['entry']) is list:
                                # Really, secondary addresses on subinterfaces?!
                                SUBIF_XIP = True
                                print(f"FOUND SUBIF WITH SECONDARY IP ADDRESS, {ifname}")
                                for subif_xip in subif['ip']['entry']:
                                    ip = subif_xip['@name']
                                    temp = garp_command.replace('IPADDRESS', ip.split('/',1)[0]) # removes anything in IP after /, ie /24
                                    temp = temp.replace('IFNAME', ifname)
                                    garp_commands.append(temp)
                                    ip_to_eth_dict.update({ip:ifname})
                            else:
                                ip = subif['ip']['entry']['@name']
                                temp = garp_command.replace('IPADDRESS', ip.split('/',1)[0]) # removes anything in IP after /, ie /24
                                temp = temp.replace('IFNAME', ifname)
                                garp_commands.append(temp)
                                ip_to_eth_dict.update({ip:ifname})
                    else:
                        print("ONLY ONE SUBIF")
                else:
                    garp_commands.append(f"No IP address found (e1)(DHCP?), {entry['@name']}")
            else:
                garp_commands.append(f"No IP address found (e2), {entry['@name']}")
    else:
        print(f"\nNo interfaces found for '{iftype}' type interfaces\n")

    return garp_commands


def garp_natrules(entries, pa_or_pan, fwconn, device_group=""):
    garp_commands = []
    global ip_to_eth_dict
    if entries:
        print(f"\n\nSearching through natrules interfaces")
        for entry in entries:
            garp_command = "test arp gratuitous ip IPADDRESS interface IFNAME"
            ip = None

            if "disabled" in entry:
                if entry["disabled"] == "yes":
                    print(f"disabled = {entry['disabled']}")
            if "destination-translation" in entry:
                #print(f"dnat = {entry['destination-translation']}")
                #print("RYAN ADD CHECK FOR INTERFACE-ADDRESS----CATCH A USE CASE.")
                garp_commands.append(f"DNAT, - Check NAT rule named: {entry['@name']} for details.")
                #obj = iterdict(entry['destination-translation'])
            if "source-translation" in entry:
                snat = entry['source-translation']
                
                # Returns Address Object typically, could also be an IP
                obj = iterdict(snat, "translated-address")
                
                # Usually 'translated-address' but check for 'interface-address'
                if obj:

                    if isinstance(obj, dict):
                        ipobjs = []
                        [ipobjs.append(o) for o in obj["member"]]

                        for ipobj in ipobjs:

                            ips = address_lookup(ipobj, pa_or_pan, device_group, fwconn)

                            for ip in ips:
                                ifname = interface_lookup(ip)
                                if not ifname:
                                    ifname = "INTERFACE NOT FOUND"
                                temp = garp_command.replace('IPADDRESS', ip.split('/',1)[0]) # removes anything in IP after /, ie /24
                                temp = temp.replace('IFNAME', ifname)    
                                garp_commands.append(temp)

                    else:
                        # Look up Address Object to get actual value
                        ips = address_lookup(obj, pa_or_pan, device_group, fwconn)

                        for ip in ips:                         
                            ifname = interface_lookup(ip)
                            if not ifname:
                                ifname = "INTERFACE NOT FOUND"
                            temp = garp_command.replace('IPADDRESS', ip.split('/',1)[0]) # removes anything in IP after /, ie /24
                            temp = temp.replace('IFNAME', ifname)    
                            garp_commands.append(temp)
                else:
                    obj = iterdict(snat, "interface-address")
                    if obj:
                        ifname = snat["dynamic-ip-and-port"]["interface-address"]["interface"]
                        if "ip" in snat["dynamic-ip-and-port"]["interface-address"]:
                            ipobj = snat["dynamic-ip-and-port"]["interface-address"]["ip"]
                            ips = address_lookup(ipobj, pa_or_pan, device_group, fwconn)
                            for ip in ips: 
                                temp = garp_command.replace('IPADDRESS', ip.split('/',1)[0]) # removes anything in IP after /, ie /24
                                temp = temp.replace('IFNAME', ifname)    
                                garp_commands.append(temp)
                        else:
                            ip = "IP NOT FOUND, ARP should be taken care of via: "
                            temp = garp_command.replace('IPADDRESS', ip.split('/',1)[0]) # removes anything in IP after /, ie /24
                            temp = temp.replace('IFNAME', ifname)    
                            garp_commands.append(temp)
                    else:
                        garp_commands.append(f"Error, SNAT configured without a translated IP (e2), {snat}")  
    else:
        print(f"No nat rules found for 'natrules")

    return garp_commands


def garp_logic(root_folder, fwconn, pa_or_pan):

    global XPATH_ADDRESS_OBJ 
    global XPATH_ADDRESS_OBJ_PAN 

    global XPATH_INTERFACES
    global XPATH_INTERFACES_PAN

    global REST_NATRULES   
    global REST_NATRULES_PAN


    global ip_to_eth_dict
    ip_to_eth_dict = {}

    device_group = None

    if pa_or_pan == "panorama":
        # Needs Template Name & Device Group
        template_name = input("\nEnter the Template Name (CORRECTLY!): ")
        device_group = input("\nEnter the Device Group Name (CORRECTLY!): ")
        
        XPATH_INTERFACES = XPATH_INTERFACES_PAN
        XPATH_INTERFACES = XPATH_INTERFACES.replace("TEMPLATE_NAME", template_name)
        XPATH_INTERFACES = XPATH_INTERFACES.replace("DEVICE_GROUP", device_group)
        REST_NATRULES = REST_NATRULES_PAN
        REST_NATRULES = REST_NATRULES.replace("TEMPLATE_NAME", template_name)
        REST_NATRULES = REST_NATRULES.replace("DEVICE_GROUP", device_group)

    # Grab Interfaces (XML)
    int_output = grab_api_output(
        root_folder, "xml", XPATH_INTERFACES, "interfaces", fwconn
    )

    # Grab NAT Rules (REST)
    nat_output = grab_api_output(
        root_folder, "rest", REST_NATRULES, "natrules", fwconn
    )

    # INTERFACES
    eth_entries = (
        int_output.get("response").get("result").get("interface").get("ethernet")
    )
    ae_entries = (
        int_output.get("response").get("result").get("interface").get("aggregate-ethernet")
    )

    eth_garp = garp_interfaces(eth_entries, "ethernet")
    ae_garp = garp_interfaces(ae_entries, "aggregate-ethernet")
    
    garp_commands =  eth_garp + ae_garp

    # Going through NAT rules

    print("\nPlease wait..\n")

    nat_entries = (
        nat_output.get("result").get("entry")
    )
    
    if device_group:
        nat_garp = garp_natrules(nat_entries, pa_or_pan, fwconn, device_group)
    else:
        nat_garp = garp_natrules(nat_entries, pa_or_pan, fwconn)

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
    obj = xmlpa.xml_api_lib_pa(pa_ip, username, password)

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
    fwconn = xmlpa.xml_api_lib_pa(pa_ip, username, password)
    garp_logic(root_folder, fwconn, pa_or_pan)
