"""
Description: 
    PA Menu
    List random XML or REST calls, print out the output. (Postman via Python)

Requires: 
    xmltodict
    json
    requests
        To install try: 'pip3 install xmltodict json requests'

Author:
    Ryan Gillespie rgillespie@compunet.biz
    Docstring stolen from Devin Callaway

Tested:
    Tested on macos 10.13.6
    Python: 3.6.2
    PA VM100, Panorama, PA 5250

Example usage:
        $ python3 pa_menu.py <destination folder> <PA(N) mgmt IP> <username>
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

import xmltodict
import json

import xml_api_lib_pa as xmlpa  # rename
import garp as garpl

# fmt: off
# Global Variables, debug & xpath location for each profile type
# ENTRY = + "/entry[@name='alert-only']"
DEBUG = False

ITEM1_XML = "/config/devices/entry[@name='localhost.localdomain']/network/interface"
ITEM1_XML_PAN = "/config/devices/entry[@name='localhost.localdomain']/template/entry[@name='TEMPLATE_NAME']/config/devices/entry[@name='localhost.localdomain']/network/interface"
ITEM2_XML = "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/rulebase/nat/rules"
ITEM2_REST =    "/restapi/9.0/Policies/NATRules?location=vsys&vsys=vsys1"
ITEM2_REST_PAN =    "/restapi/9.0/Policies/NATPostRules?location=device-group&device-group=DEVICE_GROUP"

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

    #print("\tCreated: {}\n".format(filename))


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

# Main Program
def main(output_list, root_folder, entry, pa_or_pan):

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
        device_group = None

        if output == "1":  # INTERFACES, --XML ONLY--
            # SET PROPER VARIABLES, GRAB EXTRA VALUES IF NEEDED
            XPATH_OR_RESTCALL = ITEM1_XML
            outputrequested = "interfaces"

            if pa_or_pan == "panorama":
                # Needs Template Name
                template_name = input("\nEnter the Template Name (CORRECTLY!): ")
                XPATH_OR_RESTCALL = ITEM1_XML_PAN.replace(
                    "TEMPLATE_NAME", template_name
                )

            # Grab Output (XML or REST, convert to dict.)
            api_output = grab_api_output(
                root_folder, "xml", XPATH_OR_RESTCALL, outputrequested
            )

        elif output == "2":  # NAT RULES, REST for now
            # SET PROPER VARIABLES, GRAB EXTRA VALUES IF NEEDED
            XPATH_OR_RESTCALL = ITEM2_REST
            outputrequested = "natrules"

            if pa_or_pan == "panorama":
                # Needs Device Group
                device_group = input("\nEnter the Device Group Name (CORRECTLY!): ")
                XPATH_OR_RESTCALL = ITEM2_REST_PAN.replace(
                    "DEVICE_GROUP", device_group
                )

            # Grab Output (XML or REST, convert to dict.)
            api_output = grab_api_output(
                root_folder, "rest", XPATH_OR_RESTCALL, outputrequested
            )


        elif output == "3":  # gARP, program.
            # SET PROPER VARIABLES, GRAB EXTRA VALUES IF NEEDED

            output = garpl.garp_logic(root_folder, pa_or_pan)

        else:
            print("\nHuh?. You entered {}\n".format(profile))
            continue

        print("done. create a loop here?")
        sys.exit(0)


# If run from the command line
if __name__ == "__main__":

    if sys.argv[1] == 'DEBUG':
        root_folder = 'debtest'
        fout = grab_files(root_folder)
        for fin in fout:
            parsedfile = json.loads(fin)
            print(f"fin = {parsedfile}")
            output = garpl.garp_logic(parsedfile, "rest", "natrules", "")
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

    allowed = list("123,-")  # Allowed user input
    incorrect_input = True
    while incorrect_input:
        selection = input(
            """\nWhat output would you like to display/export?

            1) List Interfaces
            2) List NAT
            3) gARP

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
    main(output_list, root_folder, entry, pa_or_pan)

    # Done!
    print("\n\nComplete!\n")
