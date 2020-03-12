"""
Description: 
    PA Gratuitous ARP Script
    Connect to PA or Panorama and determine which IP Addresses and Interfaces should
    Send Gratuitous ARP out, typically during the cutover of a new FW.

Requires:
    requests
    xmltodict
    lxml
    json
        to install try: pip3 install xmltodict requests lxml json

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

from lxml import etree
import xmltodict
import xml_api_lib_pa as xmlpa

# fmt: off
# Global Variables, debug & xpath location for each profile type
# ENTRY = + "/entry[@name='alert-only']"
DEBUG = False

XML_ADDRESS =       "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/address/entry[@name='ENTRY_NAME']"
#XML_ADDRESSGROUP =  "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/address-group/entry[@name='ENTRY_NAME']"
XML_INTERFACES =    "/config/devices/entry[@name='localhost.localdomain']/network/interface"
XML_NATRULES =      "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/rulebase/nat/rules"
REST_NATRULES =     "/restapi/9.0/Policies/NATRules?location=vsys&vsys=vsys1"

PAN_XML_ADDRESS =       "/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='DEVICE_GROUP']/address/entry[@name='ENTRY_NAME']"
#PAN_XML_ADDRESSGROUP =  "/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='lab-Branch1-dg']/address-group/entry[@name='ENTRY_NAME']"
PAN_XML_INTERFACES =    "/config/devices/entry[@name='localhost.localdomain']/template/entry[@name='TEMPLATE_NAME']/config/devices/entry[@name='localhost.localdomain']/network/interface"
PAN_XML_NATRULES =      "/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='DEVICE_GROUP']/post-rulebase/nat/rules"
PAN_REST_POSTNATRULES = "/restapi/9.0/Policies/NATPostRules?location=device-group&device-group=DEVICE_GROUP"
# fmt: on


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

    print("\tCreated: {}\n".format(filename))

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
                            print(f"ip={ip},ifname={ifname}")
                            h = ip.split('/',1)[0]
                            print(f"h={h}")
                            ip_to_eth_dict.update({ip.split('/',1)[0]:ifname})
                    else: 
                        ip = entry['layer3']['ip']['entry']['@name']
                        temp = garp_command.replace('IPADDRESS', ip.split('/',1)[0]) # removes anything in IP after /, ie /24
                        temp = temp.replace('IFNAME', ifname)
                        garp_commands.append(temp)
                        print(f"ip={ip},ifname={ifname}")
                        h = ip.split('/',1)[0]
                        print(f"h={h}")
                        ip_to_eth_dict.update({h:ifname})
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
                                    print(f"ip={ip},ifname={ifname}")
                                    h = ip.split('/',1)[0]
                                    print(f"h={h}")
                                    ip_to_eth_dict.update({ip.split('/',1)[0]:ifname})
                            else:
                                ip = subif['ip']['entry']['@name']
                                temp = garp_command.replace('IPADDRESS', ip.split('/',1)[0]) # removes anything in IP after /, ie /24
                                temp = temp.replace('IFNAME', ifname)
                                garp_commands.append(temp)
                                print(f"ip={ip},ifname={ifname}")
                                h = ip.split('/',1)[0]
                                print(f"h={h}")
                                ip_to_eth_dict.update({ip.split('/',1)[0]:ifname})
                            
                            #Append Sub Interfaces
                            # if not SUBIF_XIP:
                            #     garp_commands.append(temp)

                    else:
                        print("ONLY ONE SUBIF")
                else:
                    temp = f"No IP address found (e1), {entry['@name']}"
            else:
                temp = f"No IP address found (e2), {entry['@name']}"
    else:
        print(f"\nNo interfaces found for '{iftype}' type interfaces\n")
    
    print(f"dict1 = {ip_to_eth_dict}")
    return garp_commands

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

def address_lookup(obj):

    XPATH = XML_ADDRESS.replace("ENTRY_NAME", obj)
    print(XPATH)
    output = grab_api_output(".", "xml", XPATH, "address")
    #temp = grab_files("debtest2")[0]
    #output = xmltodict.parse(temp)

    ips = output["response"]["result"]["entry"]["ip-netmask"]
    
    print(f"ips = {ips}")
    if ips is list:
        for ip in ips:
            ips.append(ip)
    else:
        ips = [ips]
    
    return ips


def garp_natrules(entries, natrules):
    garp_commands = []
    global ip_to_eth_dict
    if entries:
        # go
        for entry in entries:
            print(f"\nName = {entry['@name']}")
            garp_command = "test arp gratuitous ip IPADDRESS interface IFNAME"
            ip = None

            print(f"dict = {ip_to_eth_dict}")

            if "disabled" in entry:
                if entry["disabled"] == "yes":
                    print(f"disabled = {entry['disabled']}")
            if "destination-translation" in entry:
                print(f"dnat = {entry['destination-translation']}")
                print("RYAN ADD CHECK FOR INTERFACE-ADDRESS----CATCH A USE CASE.")
                garp_commands.append(f"DNAT, - Check NAT rule named: {entry['@name']} for details.")
                #obj = iterdict(entry['destination-translation'])
            if "source-translation" in entry:
                snat = entry['source-translation']
                print(f"snat = {snat}")
                
                obj = iterdict(snat, "translated-address")
                
                if obj:
                    
                    print(f"Source NAT to obj = {obj}")

                    if isinstance(obj, dict):
                        ips = []
                        ifname = "iface-lookup"
                        [ips.append(o) for o in obj["member"]]

                        for ip in ips:
                            ifname = "iface-lookup"
                            temp = garp_command.replace('IPADDRESS', ip.split('/',1)[0]) # removes anything in IP after /, ie /24
                            temp = temp.replace('IFNAME', ifname)    
                            garp_commands.append(temp)

                    else:
                        ips = address_lookup(obj)
                        for ip in ips:
                            if ip.split('/',1)[0] in ip_to_eth_dict:
                                ifname = ip_to_eth_dict[ip.split('/',1)[0]]
                                print(f"HECKYA, {ip} found. {ifname}")
                            ifname = "iface-lookup"
                            temp = garp_command.replace('IPADDRESS', ip.split('/',1)[0]) # removes anything in IP after /, ie /24
                            temp = temp.replace('IFNAME', ifname)    
                            garp_commands.append(temp)
                else:
                    obj = iterdict(snat, "interface-address")
                    if obj:
                        ifname = snat["dynamic-ip-and-port"]["interface-address"]["interface"]
                        if "ip" in snat["dynamic-ip-and-port"]["interface-address"]:
                            ipobj = snat["dynamic-ip-and-port"]["interface-address"]["ip"]
                            ips = address_lookup(ipobj)
                            for ip in ips:
                                temp = garp_command.replace('IPADDRESS', ip.split('/',1)[0]) # removes anything in IP after /, ie /24
                                temp = temp.replace('IFNAME', ifname)    
                                garp_commands.append(temp)
                        else:
                            ip = "NO IP FOUND, ARP should be taken care of via: "
                            temp = garp_command.replace('IPADDRESS', ip.split('/',1)[0]) # removes anything in IP after /, ie /24
                            temp = temp.replace('IFNAME', ifname)    
                            garp_commands.append(temp)
                    else:
                        garp_commands.append(f"Error, SNAT configured without a translated IP (e2), {snat}")  
    else:
        print(f"No nat rules found for 'natrules")

    return garp_commands

def grab_api_output(root_folder, xml_or_rest, xpath_or_restcall, outputrequested):
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
            print("More error checking needed here.")
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
            print("More error checking needed here.")
            sys.exit(0)

    if not success:
        # Extra logging when debugging
        if DEBUG:
            print(f"\nGET request sent: xpath={xpath}.\n")
            print(f"\nResponse: \n{response}")
            create_xml_files(result, filename)
            print(f"Output also written to {filename}")
        else:
            print(f"\nError exporting 'interfaces' object.")
            print(
                "(Normally this just means no object found, set DEBUG=True if needed)"
            )
    if xml_or_rest == "xml":
        return xml_response
    else:
        return json_response


def garp_logic(api_output, xml_or_rest, outputrequested):

    # INTERFACES
    if outputrequested == "interfaces":
        eth_entries = (
            api_output.get("response").get("result").get("interface").get("ethernet")
        )
        ae_entries = (
            api_output.get("response").get("result").get("interface").get("aggregate-ethernet")
        )

        eth_garp = garp_interfaces(eth_entries, "ethernet")
        ae_garp = garp_interfaces(ae_entries, "aggregate-ethernet")

        garp_commands =  eth_garp + ae_garp

    elif outputrequested == "natrules":
        nat_entries = (
            api_output.get("result").get("entry")
        )

        garp_commands = garp_natrules(nat_entries, "natrules")

    return garp_commands

# Main Program
def main(output_list, root_folder, xml_or_rest, entry, pa_or_pan):

    global ip_to_eth_dict
    ip_to_eth_dict = {}

    # Organize user input
    # Expand '1' to '2,3,4,5,6,7,8,9,A'
    if "1" in output_list:
        pass
    # Expand '2-5,8-9' to '2,3,4,5,8,9'
    if "-" in output_list:
        dashes = [index for index, value in enumerate(output_list) if value == "-"]
        remaining = output_list
        final = []

        for dash in dashes:
            predash = remaining.index("-") - 1
            postdash = remaining.index("-") + 1

            up_to_predash = [x for x in remaining[:predash]]
            final = final + up_to_predash

            expanded = range(int(remaining[predash]), int(remaining[postdash]) + 1)
            final = final + [str(num) for num in expanded]

            remaining = remaining[postdash + 1 :]

        if remaining:
            output_list = final + remaining
        else:
            output_list = final

    ######
    ### Begin the real work.
    ######
    # Loop through user provided input, import each profile
    for output in output_list:
        if output == "1":  # INTERFACES, --XML ONLY--
            # SET PROPER VARIABLES, GRAB EXTRA VALUES IF NEEDED
            XPATH_OR_RESTCALL = XML_INTERFACES
            xml_or_rest = "xml"
            ext = "xml"
            outputrequested = "interfaces"

            if pa_or_pan == "panorama":
                # Needs Template Name
                template_name = input("\nEnter the Template Name (CORRECTLY!): ")
                XPATH_OR_RESTCALL = PAN_XML_INTERFACES.replace(
                    "TEMPLATE_NAME", template_name
                )

        elif output == "2":  # NAT RULES, REST for now
            # SET PROPER VARIABLES, GRAB EXTRA VALUES IF NEEDED
            XPATH_OR_RESTCALL = REST_NATRULES
            xml_or_rest = "rest"
            ext = "json"
            outputrequested = "natrules"

            if pa_or_pan == "panorama":
                # Needs Device Group
                device_group = input("\nEnter the Device Group Name (CORRECTLY!): ")
                XPATH_OR_RESTCALL = PAN_REST_POSTNATRULES.replace(
                    "DEVICE_GROUP", device_group
                )

        else:
            print("\nHuh?. You entered {}\n".format(profile))
            continue

        # Grab Output (XML or REST, convert to dict.)
        api_output = grab_api_output(
            root_folder, xml_or_rest, XPATH_OR_RESTCALL, outputrequested
        )

        # gARP Logic
        output = garp_logic(api_output, xml_or_rest, outputrequested)
        
        print(f"\ngARP {outputrequested} Test Commands:")
        print("-------------------------------------------------------------")
        for line in output:
            print(line)
        print("-------------------------------------------------------------")


# If run from the command line
if __name__ == "__main__":

    if sys.argv[1] == 'DEBUG':
        root_folder = 'debtest'
        fout = grab_files(root_folder)
        for fin in fout:
            parsedfile = json.loads(fin)
            print(f"fin = {parsedfile}")
            output = garp_logic(parsedfile, "rest", "natrules")
        print("===========DEBUG MODE===========")
        print("\ngARP DEBUG Test Commands:")
        print("-------------------------------------------------------------")
        for line in output:
            print(line)
        print("-------------------------------------------------------------")
        sys.exit(0)

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

    # MENU
    # xml_or_rest = "1"

    # while xml_or_rest != "1" and xml_or_rest != "2":
    #     xml_or_rest = input(
    #         """\nREST or XML??

    #     1) XML  (8.1-)
    #     2) REST (9.0+)

    #     Enter 1 or 2: """
    #     )

    # UNUSED PLACEHOLDER FOR NOW
    xml_or_rest = "xml"

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

    allowed = list("12,-")  # Allowed user input
    incorrect_input = True
    while incorrect_input:
        selection = input(
            """\nWhat output would you like to display/export?

            1) List Interfaces
            2) List NAT

            For multiple enter: ('1' or 2-4' or '2,5,7')

            Enter Selection: """
        )

        for value in selection:
            if value not in allowed:
                incorrect_input = True
                break
            else:
                incorrect_input = False

        temp = "".join(selection)
        if temp.endswith("-") or temp.startswith("-"):
            incorrect_input = True

    entry = ""

    # Turn input into list, remove commas
    output_list = list(selection.replace(",", ""))

    # Run program
    main(output_list, root_folder, xml_or_rest, entry, pa_or_pan)

    # Done!
    print("\n\nComplete!\n")
