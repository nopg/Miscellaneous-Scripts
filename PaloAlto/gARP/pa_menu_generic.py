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

from getpass import getpass
import sys
import os

import xmltodict
import json

import api_lib_pa as pa  # rename
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
            # if file.endswith(".xml"):
            with open(root + "/" + file, "r") as fin:
                data = fin.read()
                file_list.append(data)
    return file_list


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
            filename = f"{root_folder}/interfaces.xml"

            if pa_or_pan == "panorama":
                # Needs Template Name
                template_name = input("\nEnter the Template Name (CORRECTLY!): ")
                XPATH_OR_RESTCALL = ITEM1_XML_PAN.replace(
                    "TEMPLATE_NAME", template_name
                )

            # Grab Output (XML or REST, convert to dict.)
            api_output = obj.grab_api_output("xml", XPATH_OR_RESTCALL, filename)
            print(api_output)

        elif output == "2":  # NAT RULES, REST for now
            # SET PROPER VARIABLES, GRAB EXTRA VALUES IF NEEDED
            XPATH_OR_RESTCALL = ITEM2_REST
            filename = f"{root_folder}/natrules.json"

            if pa_or_pan == "panorama":
                # Needs Device Group
                device_group = input("\nEnter the Device Group Name (CORRECTLY!): ")
                XPATH_OR_RESTCALL = ITEM2_REST_PAN.replace("DEVICE_GROUP", device_group)

            # Grab Output (XML or REST, convert to dict.)
            api_output = obj.grab_api_output("rest", XPATH_OR_RESTCALL, filename)
            print(api_output)

        elif output == "3":  # gARP, program.
            # Run gARP
            garpl.garp_logic(pa_ip, username, password, pa_or_pan, root_folder)

        else:
            print("\nHuh?. You entered {}\n".format(output))
            continue

        print("done. create a loop here?")
        sys.exit(0)


# If run from the command line
if __name__ == "__main__":

    root_folder = None
    if len(sys.argv) == 2:
        if sys.argv[1] == "DEBUG":
            sys.exit(0)
    elif len(sys.argv) == 4:
        root_folder = sys.argv[3]
    elif len(sys.argv) != 3:
        print("\nplease provide the following arguments:")
        print("\tpython3 garp.py <PA/Panorama IP> <username> <optional output folder>\n\n")
        sys.exit(0)

    # Gather input
    pa_ip = sys.argv[1]
    username = sys.argv[2]
    password = getpass("Enter Password: ")
    if not root_folder:
        root_folder = "~temp/"

    # Create connection with the Palo Alto as 'obj'
    obj = pa.api_lib_pa(pa_ip, username, password)

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
