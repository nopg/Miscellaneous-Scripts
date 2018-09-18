"""
Description: 
    Import/Export Security Profile objects using the Palo Alto API
    Export - Exports chosen objects to appropriate files
    Import - Imports from root_folder all chosen objects

Requires:
    requests
    xmltodict
        to install try: pip3 install xmltodict requests 

Author:
    Ryan Gillespie rgillespie@compunet.biz
    Docstring stolen from Devin Callaway

Tested:
    Tested on macos 10.12.3
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

    # Because XML: remove <response/><result/> and <?xml> tags
    # Using get().get() won't cause exception on KeyError
    data = temp.get("response").get("result")
    if data:
        data = xmltodict.unparse(data)
    else:
        data = xmltodict.unparse(temp)
    data = data.replace('<?xml version="1.0" encoding="utf-8"?>', "")

    with open(filename, "w") as fout:
        fout.write(data)


# Imports profiles into Palo Alto API based on profile type
def import_profile_objects(root_folder, profile_type, xpath):

    # Rename 'virus' folder to 'antivirus' (just makes more sense)
    if profile_type == "virus":
        new_root = f"{root_folder}/antivirus"
    else:
        new_root = f"{root_folder}/{profile_type}"

    # Gather all files, returns string containing xml
    files = grab_files_read(new_root)

    if not files:
        print(f"\nNo {profile_type} objects were found!")

    # Because: xml.
    # Create root tags (i.e. <virus>, </spyware>, etc)
    # Remove 'custom/' for custom objects
    formatted_profile_type = profile_type.replace("custom/", "")
    root_tag = f"<{formatted_profile_type}>"
    root_tag_end = f"</{formatted_profile_type}>"

    for xml in files:
        # Because: xml.
        # Remove root tag (i.e. <virus>, </spyware>, etc)
        entry_element = xml.replace(root_tag, "")
        entry_element = entry_element.replace(root_tag_end, "")

        # Import xml via Palo Alto API
        response = obj.get_request_pa(
            call_type="config", action="set", xpath=xpath, element=entry_element
        )

        # Print out result
        result = xmltodict.parse(response)
        if result["response"]["@status"] == "success":
            print(f"\nImported {profile_type} object.")
        else:
            # Extra logging when debugging
            if DEBUG:
                print(f"\nGET request sent: xpath={xpath}.\n element={entry_element}\n")
                print(f"\nResponse: \n{response}")
            else:
                print(f"\nError importing {profile_type} object.")


# Grab profile from Palo Alto API based on profile type
def export_profile_objects(destination_folder, profile_type, xpath):

    # remove 'custom/' out of filename for custom objects
    formatted_profile_type = profile_type.replace("custom/", "")

    # Rename 'virus' folder to 'antivirus' (just makes more sense)
    if profile_type == "virus":
        new_destination = f"{destination_folder}/antivirus"
        filename = f"{new_destination}/antivirus-profiles.xml"
    else:
        new_destination = f"{destination_folder}/{profile_type}"
        filename = f"{new_destination}/{formatted_profile_type}-profiles.xml"

    # Create the root folder and subfolder if it doesn't exist
    os.makedirs(new_destination, exist_ok=True)

    # Export xml via Palo Alto API
    response = obj.get_request_pa(call_type="config", action="show", xpath=xpath)

    # Print out result
    result = xmltodict.parse(response)
    if result["response"]["@status"] == "success":
        entries = result["response"]["result"][formatted_profile_type]
        if entries:
            # Create file
            write_data_output(result, filename)
            print(f"\nExported {profile_type} object.")
        else:
            print(f"No objects found for {profile_type}.")
    else:
        # Extra logging when debugging
        if DEBUG:
            print(f"\nGET request sent: xpath={xpath}.\n")
            print(f"\nResponse: \n{response}")
            write_data_output(result,filename)
            print(f"Output also written to {filename}")
        else:
            print(f"\nError exporting {profile_type} object.")
            print(
                "(Normally this just means no object found, set DEBUG=True if needed)"
            )


# Main Program
def main(profile_list, root_folder, selection):

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

    # 1 = Export, 2 = Import
    if selection == "1":
        wrapper_call = export_profile_objects
    else:
        wrapper_call = import_profile_objects

    # Loop through user provided input, import each profile
    for profile in profile_list:
        if profile == "2":
            wrapper_call(root_folder, "virus", ANTIVIRUS)
        elif profile == "3":
            wrapper_call(root_folder, "custom/spyware", SPYWARESIG)
            wrapper_call(root_folder, "spyware", SPYWARE)
        elif profile == "4":
            wrapper_call(root_folder, "custom/vulnerability", VULNERABLESIG)
            wrapper_call(root_folder, "vulnerability", VULNERABILITY)
        elif profile == "5":
            wrapper_call(root_folder, "custom/custom-url-category", URLCATEGORY)
            wrapper_call(root_folder, "url-filtering", URLFILTERING)
        elif profile == "6":
            wrapper_call(root_folder, "file-blocking", FILEBLOCKING)
        elif profile == "7":
            wrapper_call(root_folder, "wildfire-analysis", WILDFIRE)
        elif profile == "8":
            wrapper_call(root_folder, "custom/data-objects", DATAPATTERN)
            wrapper_call(root_folder, "data-filtering", DATAFILTERING)
        elif profile == "9":
            wrapper_call(root_folder, "dos-protection", DDOS)
        else:
            print("\nHuh?. You entered {}\n".format(profile))
            continue


# If run from the command line
if __name__ == "__main__":

    # Guidance on how to use the script
    if len(sys.argv) != 4:
        print("\nplease provide the following arguments:")
        print(
            "\tpython3 pa_security_profiles.py <root folder for import/export> <PA mgmt IP> <username>\n\n"
        )
        sys.exit(0)

    # Gather input
    root_folder = sys.argv[1]
    pa_ip = sys.argv[2]
    username = sys.argv[3]
    password = getpass.getpass("Enter Password: ")

    # Create connection with the Palo Alto as 'obj'
    obj = pa.rest_api_lib_pa(pa_ip, username, password)

    # MENU
    export_or_import = ""
    while export_or_import != "1" and export_or_import != "2":
        export_or_import = input(
            """\nWhat would you like to do?

        1) EXPORT security-profile objects (From PA into xml)
        2) IMPORT security-profile objects (From xml into PA)

        Enter 1 or 2: """
        )

    selection = input(
        """\nWhat type of security profiles to import?

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
    main(profile_list, root_folder, export_or_import)

    # Done!
    print("\n\nComplete!\n")
