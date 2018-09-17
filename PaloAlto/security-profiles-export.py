"""
Docstring stolen from Devin Callaway

Discription: 
    Import/Export Security Profile objects using the Palo Alto API
    Export - Exports chosen objects to appropriate files
    Import - Imports from root_folder all chosen objects

Requires:
    requests
    xmltodict
        to install try: pip3 install xmltodict requests 

Author:
    Ryan Gillespie rgillespie@compunet.biz

Tested:
    Tested on macos 10.12.3
    Python: 3.6.2
    PA VM100

Example usage:
        $ python3 dh-security-profiles-export.py <destination folder> <PA mgmt IP> <username>
        Password: 

Cautions:
    - Will export ONLY COMMITTED CHANGES.
        To export candidate configuration change action="show" to action="get" (not recommended)
    - When no objects are found, sometimes the PA returns an error, sometimes it returns 'success' with 'node not found'. 
    - Will NOT commit any changes, this must be done manually.
    - Set DEBUG=True if errors occur and you would like detailed information.

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
import xml.etree.ElementTree as etree

import xmltodict
import rest_api_lib_pa as pa


# fmt: off
# Global Variables, debug & xpath location for each profile type
# ENTRY = + "/entry[@name='alert-only']"
DEBUG = False
ANTIVIRUS =     "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/virus"
SPYWARE =       "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/spyware"
SPYWARESIG =    "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/threats/spyware"
VULNERABILITY = "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/vulnerability"
VULNERABLESIG = "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/threats/vulnerability"
URLFILTERING =  "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/url-filtering"
URLCATEGORY =   "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/custom-url-category"
FILEBLOCKING =  "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/file-blocking"
WILDFIRE =      "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/wildfire-analysis"
DATAFILTERING = "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/data-filtering"
DATAPATTERN =   "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/data-objects"
DDOS =          "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/dos-protection"
# fmt: on

# Create file for each profile type
def write_etree_output(data, filename):

    with open(filename, "w") as fout:
        fout.write(data)


# Grab profile from Palo Alto API based on profile type
def find_profile_objects(destination_folder, profile_type, xpath):

    f_profile_type = profile_type.replace("threats/", "")

    # Rename 'virus' folder to 'antivirus' (just makes more sense)
    if profile_type == "virus":
        new_destination = destination_folder + "/antivirus"
        filename = new_destination + "/antivirus-profiles.xml"
    else:
        new_destination = destination_folder + "/" + profile_type

        # remove 'threats/' out of filename for custom objects
        if "threats" in profile_type:
            filename = new_destination + "/" + f_profile_type + "-profiles.xml"
        else:
            filename = new_destination + "/" + profile_type + "-profiles.xml"

    # Create the folder under root folder if it doesn't exist
    os.makedirs(new_destination, exist_ok=True)

    # Export xml via Palo Alto API
    response = obj.get_request_pa(call_type="config", action="show", xpath=xpath)

    # Print out result
    result = xmltodict.parse(response)

    if result["response"]["@status"] == "success":
        entries = result["response"]["result"][f_profile_type]
        if not entries:
            print(f"No objects found for {profile_type}.")
        else:
            # Create file
            # Because XML: remove <response/><result/> and <?xml> tags
            output = result["response"]["result"]
            output = xmltodict.unparse(output)
            output = output.replace('<?xml version="1.0" encoding="utf-8"?>', "")

            write_etree_output(output, filename)
            print(f"\nExported {profile_type} object.")
    else:
        if DEBUG:
            print(f"\nGET request sent: xpath={xpath}.\n")
            print(response)
        else:
            print(f"Error exporting {profile_type} object.")
            print(
                "(Normally this just means no object found, set DEBUG=True if needed)"
            )


def main(profile_list, destination_folder):

    # Organize user input
    # Expand '1' to '2,3,4,5,6,7,8,9'
    if "1" in profile_list:
        profile_list = [str(x) for x in range(2, 10)]
    # Expand '2-5' to '2,3,4,5'
    if "-" in profile_list:
        start = int(profile_list[0])
        end = profile_list[-1:]
        end = int(end[0]) + 1
        profile_list = [str(x) for x in range(start, end)]

    # Loop through user provided input, import each profile
    for profile in profile_list:

        if profile == "2":
            find_profile_objects(destination_folder, "virus", ANTIVIRUS)
        elif profile == "3":
            find_profile_objects(destination_folder, "threats/spyware", SPYWARESIG)
            find_profile_objects(destination_folder, "spyware", SPYWARE)
        elif profile == "4":
            # fmt: off
            find_profile_objects(destination_folder, "threats/vulnerability", VULNERABLESIG)
            # fmt: on
            find_profile_objects(destination_folder, "vulnerability", VULNERABILITY)
        elif profile == "5":
            find_profile_objects(destination_folder, "custom-url-category", URLCATEGORY)
            find_profile_objects(destination_folder, "url-filtering", URLFILTERING)
        elif profile == "6":
            find_profile_objects(destination_folder, "file-blocking", FILEBLOCKING)
        elif profile == "7":
            find_profile_objects(destination_folder, "wildfire-analysis", WILDFIRE)
        elif profile == "8":
            find_profile_objects(destination_folder, "data-objects", DATAPATTERN)
            find_profile_objects(destination_folder, "data-filtering", DATAFILTERING)
        elif profile == "9":
            find_profile_objects(destination_folder, "dos-protection", DDOS)
        else:
            print("\nHuh?. You entered {}\n".format(profile))
            continue


# If run from the command line
if __name__ == "__main__":

    # Guidance on how to use the script
    if len(sys.argv) != 4:
        print("\nplease provide the following arguments:")
        print(
            "\tpython3 security-profiles-export.py <destination folder> <PA mgmt IP> <username>\n\n"
        )
        sys.exit(0)

    # Gather input
    destination_folder = sys.argv[1]
    pa_ip = sys.argv[2]
    username = sys.argv[3]
    password = getpass.getpass("Enter Password: ")

    # Create connection with the Palo Alto as 'obj'
    obj = pa.rest_api_lib_pa(pa_ip, username, password)

    # MENU
    selection = input(
        """\nWhat type of security profiles to export?

                1) ALL Profiles
                2) Antivirus
                3) Anti-Spyware
                4) Vulnerability Protection
                5) URL Filtering
                6) File Blocking
                7) Wildfire Analysis
                8) Data Filtering
                9) DoS Protection

                For multiple enter: ('1' or 2-4' or '2,5,7')

                Enter Selection: """
    )

    # Turn input into list, remove commas
    profile_list = list(selection.replace(",", ""))

    # Run program
    main(profile_list, destination_folder)

    # Done!
    print("\n\nComplete!\n")
