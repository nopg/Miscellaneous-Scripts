"""
Description: 
    Import/Export Security Profile objects using the Palo Alto API
    Export - Exports chosen objects to appropriate files
    Import - Imports from root_folder all chosen objects

Requires:
    requests
    xmltodict
    lxml
        to install try: pip3 install xmltodict requests lxml

Author:
    Ryan Gillespie rgillespie@compunet.biz
    Docstring stolen from Devin Callaway

Tested:
    Tested on macos 10.12.3, Windows 10
    Python: 3.6.2
    PA VM100

Example usage:
        $ python3 pa_security_profiles.py <destination folder> <PA mgmt IP> <username>
        Password: 

Cautions:
    - Set DEBUG=True if errors occur and you would like detailed information.
    - Will export ONLY COMMITTED CHANGES.
        To export candidate configuration change action="show" to action="get" (not recommended)
    - Will NOT commit any imported objects, this must be done manually.
    

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

# import rest_api_lib_pa as restpa


# fmt: off
# Global Variables, debug & xpath location for each profile type
# ENTRY = + "/entry[@name='alert-only']"
DEBUG = False

XML_INTERFACES =    "/config/devices/entry[@name='localhost.localdomain']/network/interface"
XML_NATRULES =      "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/rulebase/nat/rules"
REST_NATRULES =     "/restapi/9.0/Policies/NATRules?location=vsys&vsys=vsys1"

PAN_XML_INTERFACES = "/config/devices/entry[@name='localhost.localdomain']/template/entry[@name='TEMPLATE_NAME']/config/devices/entry[@name='localhost.localdomain']/network/interface"
PAN_XML_NATRULES = "/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='DEVICE_GROUP']/post-rulebase/nat/rules"
PAN_REST_POSTNATRULES = "/restapi/9.0/Policies/NATPostRules?location=device-group&device-group=DEVICE_GROUP"
# fmt: on


# Read all .xml files found in folder_name, return list containing all the output
def grab_xml_files(folder_name):
    profile_objects = []
    for root, dirs, files in os.walk(folder_name):
        for file in files:
            if file.endswith(".xml"):
                with open(root + "/" + file, "r") as fin:
                    data = fin.read()
                    profile_objects.append(data)
    return profile_objects


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
    fout = open(filename, "w")
    fout.write(json.dumps(data))
    fout.close()

    print("\tCreated: {}\n".format(filename))

def garp_interfaces(entries, iftype):

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
                    else: 
                        ip = entry['layer3']['ip']['entry']['@name']
                        temp = garp_command.replace('IPADDRESS', ip.split('/',1)[0]) # removes anything in IP after /, ie /24
                        temp = temp.replace('IFNAME', ifname)
                        garp_commands.append(temp)
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
                            else:
                                ip = subif['ip']['entry']['@name']
                                temp = garp_command.replace('IPADDRESS', ip.split('/',1)[0]) # removes anything in IP after /, ie /24
                                temp = temp.replace('IFNAME', ifname)
                                garp_commands.append(temp)
                            
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
    
    return garp_commands


def garp_natrules(entries, natrules):
    garp_commands = []

    if entries:
        # go
        for entry in entries:
            print()
            print(f"name = {entry['@name']}")
            print(f"oSrczone = {entry['from']['member']}")
            print(f"oDstzone = {entry['to']['member']}")
            print(f"destination = {entry['destination']}")
            if "disabled" in entry:
                print(f"disabled = {entry['disabled']}")
            if "destination-translation" in entry:
                print(f"dnat = {entry['destination-translation']}")
            if "source-translation" in entry:
                print(f"snat = {entry['source-translation']}")
            if "to-interface" in entry:
                print(f"to-interface = {entry['to-interface']}")

            print()
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
                "Nothing found on PA, are you connecting to the right device? Check output for XML API reply"
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
                "Nothing found on PA, are you connecting to the right device? Check output for REST API reply"
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
        xml = grab_xml_files(root_folder)
        parsedxml = xmltodict.parse(xml[0])
        print(f"xml = {parsedxml}")
        output = garp_logic(parsedxml, "xml", "interfaces")
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
