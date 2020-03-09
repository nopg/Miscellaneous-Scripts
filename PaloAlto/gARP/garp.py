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
XML_INTERFACES =    "/config/devices/entry[@name='localhost.localdomain']/network/interface/ethernet"
XML_NATRULES =      "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/rulebase/nat/rules"
REST_NATRULES =     "/restapi/9.0/Policies/NATRules?location=vsys&vsys=vsys1"
# fmt: on


# Read all .xml files found in folder_name, return list containing all the output
def grab_files_read(folder_name):
    profile_objects = []
    for root, dirs, files in os.walk(folder_name):
        for file in files:
            if file.endswith(".xml"):
                with open(root + "/" + file, "r") as fin:
                    data = fin.read()
                    profile_objects.append(data)
    return profile_objects


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
        data = temp.get("response").get("result")
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
def show_objects_interfaces(destination_folder, rest_or_xml, xpath_or_call):

    # Set filename
    filename = f"{destination_folder}/interfaces.xml"

    # Export xml via Palo Alto API
    response = obj.get_request_pa(call_type="config", action="show", xpath=xpath_or_call)

    # Print out result
    result = xmltodict.parse(response)
    if result["response"]["@status"] == "success":

        # Check if one specific was searched or the entire list
        entry = result.get("response").get("result").get("entry")
        ###################### MUST BE UPDATED ###############
        entries = result.get("response").get("result").get("ethernet")

        if entry:
            # Set filename to entry name
            object_name = result["response"]["result"]["entry"]["@name"]
            filename = f"{destination_folder}/{object_name}.xml"
            # Add root tags (i.e. <spyware>), for clarity.
            # API doesn't return these tags on entry-specific requests
            temp = result["response"]["result"]
            data = {"interfaces": temp}
            # Create file
            write_data_output(data, filename)
            print(f"\nExported 'interfaces' object.")
        elif entries:
            # Create file
            write_data_output(result, filename)
            print(f"\nExported 'interfaces' object.")
        else:
            print(f"No objects found for 'interfaces")
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

# Grab interfaces from Palo Alto API
def show_objects_natrules(destination_folder, rest_or_xml, xpath_or_call):

    # Set filename
    filename = f"{destination_folder}/natrules.json"

    # Export xml via Palo Alto API
    response = obj.get_rest_request_pa(call=xpath_or_call)

    json_response = json.loads(response)
    data = json_response["result"]

    create_json_files(data, filename)

    # # Print out result
    # result = xmltodict.parse(response)
    # if result["response"]["@status"] == "success":

    #     # Check if one specific was searched or the entire list
    #     entry = result.get("response").get("result").get("entry")
    #     ###################### MUST BE UPDATED ###############
    #     entries = result.get("response").get("result").get("ethernet")

    #     if entry:
    #         # Set filename to entry name
    #         object_name = result["response"]["result"]["entry"]["@name"]
    #         filename = f"{destination_folder}/{object_name}.xml"
    #         # Add root tags (i.e. <spyware>), for clarity.
    #         # API doesn't return these tags on entry-specific requests
    #         temp = result["response"]["result"]
    #         data = {"interfaces": temp}
    #         # Create file
    #         write_data_output(data, filename)
    #         print(f"\nExported 'interfaces' object.")
    #     elif entries:
    #         # Create file
    #         write_data_output(result, filename)
    #         print(f"\nExported 'interfaces' object.")
    #     else:
    #         print(f"No objects found for 'interfaces")
    # else:
    #     # Extra logging when debugging
    #     if DEBUG:
    #         print(f"\nGET request sent: xpath={xpath}.\n")
    #         print(f"\nResponse: \n{response}")
    #         write_data_output(result, filename)
    #         print(f"Output also written to {filename}")
    #     else:
    #         print(f"\nError exporting 'interfaces' object.")
    #         print(
    #             "(Normally this just means no object found, set DEBUG=True if needed)"
    #         )


def rest_func():
    pass
def xml_func():
    pass

# Main Program
def main(output_list, root_folder, selection, entry):

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

    # 1 = REST, 2 = API -- CURRENTLY UNUSED
    if selection == "1":
        wrapper_call = rest_func
    else:
        wrapper_call = xml_func

    # Loop through user provided input, import each profile
    for output in output_list:
        if output == "1":
            show_objects_interfaces(root_folder, "xml", XML_INTERFACES)
        elif output == "2":
            show_objects_natrules(root_folder, "rest", REST_NATRULES)
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

    while rest_or_xml != "1" and export_or_import != "2":
        rest_or_xml = input(
            """\nREST or XML??

        1) REST (9.0+)
        2) XML (8.1-)

        Enter 1 or 2: """
        )

    allowed = list("12")  # Allowed user input
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

    # ENTRY SELECTION - WHEN NEEDED
    # if len(selection) == 1 and selection != "1":
    #     entry = input(
    #         """\n
    #         (Blank line for all objects)
    #         Enter a specific object name: """
    #     )
    #     # Check if a specific object was requested
    #     if entry:
    #         entry = f"/entry[@name='{entry}']"
    # else:
    #     entry = ""

    entry = ""

    # Turn input into list, remove commas
    output_list = list(selection.replace(",", ""))

    # Run program
    main(output_list, root_folder, rest_or_xml, entry)

    # Done!
    print("\n\nComplete!\n")
