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
import rest_api_lib_pa as restpa


# fmt: off
# Global Variables, debug & xpath location for each profile type
# ENTRY = + "/entry[@name='alert-only']"
DEBUG = False
# ANTIVIRUS =     "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/virus"
# SPYWARE =       "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/spyware"
# SPYWARESIG =    "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/threats/spyware"
# VULNERABILITY = "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/vulnerability"
# VULNERABLESIG = "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/threats/vulnerability"
# URLFILTERING =  "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/url-filtering"
# URLCATEGORY =   "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/custom-url-category"
# FILEBLOCKING =  "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/file-blocking"
# WILDFIRE =      "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/wildfire-analysis"
# DATAFILTERING = "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/data-filtering"
# DATAPATTERN =   "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/data-objects"
# DDOS =          "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/dos-protection"
# PROFILEGROUP =  "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profile-group"
XML_INTERFACES =    "/config/devices/entry[@name='localhost.localdomain']/network/interface"
XML_NATRULES =      "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/rulebase/nat/rules"
REST_NATRULES =     "/restapi/9.0/Policies/NATRules?location=vsys&vsys=vsys1"

PAN_XML_INTERFACES = "/config/devices/entry[@name='localhost.localdomain']/template/entry[@name='TEMPLATE_NAME']/config/devices/entry[@name='localhost.localdomain']/network/interface"
PAN_XML_NATRULES = "/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='DEVICE_GROUP']/post-rulebase/nat/rules"
PAN_REST_POSTNATRULES = "/restapi/9.0/Policies/NATPostRules?location=device-group&device-group=DEVICE_GROUP"
# fmt: on


# # Read all .xml files found in folder_name, return list containing all the output
# def grab_files_read(folder_name):
#     profile_objects = []
#     for root, dirs, files in os.walk(folder_name):
#         for file in files:
#             if file.endswith(".xml"):
#                 with open(root + "/" + file, "r") as fin:
#                     data = fin.read()
#                     profile_objects.append(data)
#     return profile_objects


# Create file for each profile type
def write_data_output(temp, filename):

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
        #data = temp.get("response").get("result")
        data = {"root": data}
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

# Grab interfaces from Palo Alto API
def pan_get_objects(destination_folder, rest_or_xml, xpath_or_call, outputrequested):

    REST = False
    XML = False

    if rest_or_xml == "rest":
        ext = "json"
        REST = True
    elif rest_or_xml == "xml":
        ext = "xml"
        XML = True

    # Set filename
    filename = f"{destination_folder}/{outputrequested}.{ext}"

    # Export xml via Palo Alto API
    success = False
    if XML: 
        response = obj.get_request_pa(call_type="config", action="get", xpath=xpath_or_call)
        result = xmltodict.parse(response)
        if result["response"]["@status"] == "success":
            success = True
        write_data_output(result, filename)
        if not result["response"]["result"]:
            print("Nothing found on Panorama, are you connecting to the right device? Check output for XML API reply")
            sys.exit(0)

    elif REST:
        response = obj.get_rest_request_pa(restcall=xpath_or_call)
        json_response = json.loads(response)
        if json_response["@status"] == "success":
            success = True
        create_json_files(response, filename)
        if not json_response["result"]:
            print("Nothing found on Panorama, are you connecting to the right device? Check output for REST API reply")
            sys.exit(0)

    if success:
        pass
    
    else:
        # Extra logging when debugging
        if DEBUG:
            print(f"\nGET request sent: xpath={xpath}.\n")
            print(f"\nResponse: \n{response}")
            write_data_output(result, filename)
            print(f"Output also written to {filename}")
        else:
            print(f"\nError exporting 'interfaces' object.")
            print(
                "(Normally this just means no object found, set DEBUG=True if needed)"
            )
    # Print out result
    if outputrequested == "interfaces":
    # INTERFACES
        print(f"result = {result}")
        ###################### MUST BE UPDATED ###############
        entries = result.get("response").get("result").get("interface").get("ethernet")

        if entries:
            # FIND INTERFACE TYPES AND SEARCH
            for entry in entries['entry']:
                if "ip" in entry['layer3']:
                    print(f"{entry['layer3']['ip']}") 
                if "dhcp-client" in entry['layer3']:
                    print(f"{entry['layer3']['dhcp-client']}") 
        else:
            print(f"No objects found for 'interfaces")

    elif outputrequested == "natrules":
        entries = json_response.get("result").get("entry")

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
            print(f"No objects found for 'natrules")


def pa_get_objects(destination_folder, rest_or_xml, xpath_or_call, outputrequested):

    REST = False
    XML = False

    if rest_or_xml == "rest":
        ext = "json"
        REST = True
    elif rest_or_xml == "xml":
        ext = "xml"
        XML = True

    # Set filename
    filename = f"{destination_folder}/{outputrequested}.{ext}"

    # Export xml via Palo Alto API
    success = False
    if XML: 
        response = obj.get_request_pa(call_type="config", action="get", xpath=xpath_or_call)
        result = xmltodict.parse(response)
        if result["response"]["@status"] == "success":
            success = True
            write_data_output(result, filename)
            if not result["response"]["result"]:
                print("Nothing found on PA, are you connecting to the right device? Check output for XML API reply")
                sys.exit(0)
    if REST:
        response = obj.get_rest_request_pa(restcall=xpath_or_call)
        json_response = json.loads(response)
        if json_response["@status"] == "success":
            success = True
            create_json_files(response, filename)
            if not json_response["response"]["result"]:
                print("Nothing found on PA, are you connecting to the right device? Check output for REST API reply")
                sys.exit(0)
    if success:
        pass
    else:
        # Extra logging when debugging
        if DEBUG:
            print(f"\nGET request sent: xpath={xpath}.\n")
            print(f"\nResponse: \n{response}")
            write_data_output(result, filename)
            print(f"Output also written to {filename}")
        else:
            print(f"\nError exporting 'interfaces' object.")
            print(
                "(Normally this just means no object found, set DEBUG=True if needed)"
            )
    # Print out result
    if outputrequested == "interfaces":
    # INTERFACES
        ###################### MUST BE UPDATED ###############
        entries = result.get("response").get("result").get("interface").get("ethernet")

        if entries:
            # FIND INTERFACE TYPES AND SEARCH
            for entry in result["response"]["result"]['interface']['ethernet']['entry']:
                if "ip" in entry['layer3']:
                    print(f"{entry['layer3']['ip']}") 
                if "dhcp-client" in entry['layer3']:
                    print(f"{entry['layer3']['dhcp-client']}") 
        else:
            print(f"No objects found for 'interfaces")

    elif outputrequested == "natrules":
        entries = json_response.get("result").get("entry")

        if entries:
            # go
            for entry in entries:
                print()
                print(f"name = {entry['@name']}")
                print(f"oSrczone = {entry['from']['member']}")
                print(f"oDstzone = {entry['to']['member']}") 
                print(f"destination = {entry['destination']}")
                print(f"disabled = {entry['disabled']}")
                if "destination-translation" in entry:
                    print(f"dnat = {entry['destination-translation']}")
                if "source-translation" in entry:
                    print(f"snat = {entry['source-translation']}")
                if "to-interface" in entry:
                    print(f"to-interface = {entry['to-interface']}")

                print()
        else:
            print(f"No objects found for 'natrules")



# Main Program
def main(output_list, root_folder, selection, entry, pa_or_pan):

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

    # 1 = PA, 2 = PAN
    if pa_or_pan == "1":
        wrapper_call = pa_get_objects
    else:
        wrapper_call = pan_get_objects


    # Loop through user provided input, import each profile
    for output in output_list:
        if output == "1":
            if pa_or_pan == "2":
                template_name = input("\nEnter the Template Name (CORRECTLY!): " )
                XPATH = PAN_XML_INTERFACES.replace('TEMPLATE_NAME', template_name)
            else:
                XPATH = XML_INTERFACES

            wrapper_call(root_folder, "xml", XPATH, "interfaces")

        elif output == "2":
            if pa_or_pan == "2":
                device_group = input("\nEnter the Device Group Name (CORRECTLY!): ")
                XPATH = PAN_REST_POSTNATRULES.replace('DEVICE_GROUP', device_group)
            else:
                XPATH = REST_NATRULES

            wrapper_call(root_folder, "rest", XPATH, "natrules")

        else:
            print("\nHuh?. You entered {}\n".format(profile))
            continue


# If run from the command line
if __name__ == "__main__":

    # Guidance on how to use the script
    if len(sys.argv) != 4:
        print("\nplease provide the following arguments:")
        print(
            "\tpython3 garp.py <output folder location> <PA mgmt IP> <username>\n\n"
        )
        sys.exit(0)

    # Gather input
    root_folder = sys.argv[1]
    pa_ip = sys.argv[2]
    username = sys.argv[3]
    password = getpass.getpass("Enter Password: ")

    # Create connection with the Palo Alto as 'obj'
    obj = xmlpa.xml_api_lib_pa(pa_ip, username, password)

    # MENU
    rest_or_xml = "1"

    while rest_or_xml != "1" and rest_or_xml != "2":
        rest_or_xml = input(
            """\nREST or XML??

        1) REST (9.0+)
        2) XML (8.1-)

        Enter 1 or 2: """
        )
        rest_or_xml = "1"

    allowed = list("12")  # Allowed user input
    incorrect_input = True
    while incorrect_input:
        pa_or_pan = input(
            """\nConnect to PA or Panorama?

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
    main(output_list, root_folder, rest_or_xml, entry, pa_or_pan)

    # Done!
    print("\n\nComplete!\n")
