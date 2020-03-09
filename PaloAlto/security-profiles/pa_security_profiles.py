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
import xml_api_lib_pa as pa


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
PROFILEGROUP =  "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profile-group"
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


# Imports profiles into Palo Alto API based on profile type
def import_profile_objects(root_folder, profile_type, xpath):

    # Add subfolder to path
    new_root = f"{root_folder}/{profile_type}"

    # Gather all files, returns string containing xml
    files = grab_files_read(new_root)
    if not files:
        print(f"\nNo {profile_type} object files were found in {new_root}!")
        return

    # Because: xml.
    # Create root tags (i.e. <virus>, </spyware>, etc)
    # Remove 'custom/' for custom objects
    # API uses 'virus' instead of 'antivirus'
    formatted_profile_type = profile_type.replace("custom/", "")
    api_profile_type = formatted_profile_type.replace("antivirus", "virus")
    root_tag = f"<{api_profile_type}>"
    root_tag_end = f"</{api_profile_type}>"

    # Check xpath to see if we are searching for a specific object name
    index = xpath.rfind("/")  # Find last section of xpath
    entry_or_profile = xpath[index:]
    entry_found = entry_or_profile.find("/entry[@name='")
    # Find the actual entry name
    if entry_found != -1:
        entry_name = entry_or_profile.replace("/entry[@name='", "")
        entry_name = entry_name.replace("']", "")

    everfound = False
    for xml in files:
        iterfound = False
        # Search for specific entry, if -1 we are grabbing all entries
        if entry_found == -1:
            # Not Found, continue as normal and grab all objects
            # Remove root tag (i.e. <virus>, </spyware>, etc)
            entry_element = xml.replace(root_tag, "")
            entry_element = entry_element.replace(root_tag_end, "")
            everfound = True
        else:
            # LXML to loop through each main <entry>, find the one with "name" matching entry_name and then
            # Assigning the correct string to entry_element. This removes the root <entry> tag by using entry[0]
            # API expects the /entry[@name='']> in the xpath, but NOT in the actual import url (xml &element=<../>)
            xmltree = etree.XML(xml)
            for entry in xmltree.getroot():
                if entry.attrib["name"] == entry_name:
                    if everfound == True:
                        print(
                            f"Error: multiple objects found with the name {entry_name}."
                        )
                        sys.exit(0)
                    everfound = iterfound = True
                    entry_element = etree.tostring(entry[0]).decode()
            if not iterfound:
                # Move to next xml file
                continue

        # Import xml via Palo Alto API
        response = obj.get_request_pa(
            call_type="config", action="set", xpath=xpath, element=entry_element
        )

        # Print out result
        result = xmltodict.parse(response)
        if result["response"]["@status"] == "success":
            if DEBUG:
                print(f"\nGET request sent: xpath={xpath}.\n Element={entry_element}\n")
                print(f"\nResponse: \n{response}")
            else:
                print(f"\nImported {profile_type} object.")
        else:
            # Extra logging when debugging
            if DEBUG:
                print(f"\nGET request sent: xpath={xpath}.\n Element={entry_element}\n")
                print(f"\nResponse: \n{response}")
            else:
                print(f"\nError importing {profile_type} object.")

    # Done looping through files, check if anything was found.
    if not everfound:
        print(f"Object {entry_name} not found in {new_root}!")


# Grab profile from Palo Alto API based on profile type
def export_profile_objects(destination_folder, profile_type, xpath):

    # remove 'custom/' out of filename for custom objects
    formatted_profile_type = profile_type.replace("custom/", "")

    # Set filename & api string (I renamed 'virus' to antivirus for files & clarity)
    filename = (
        f"{destination_folder}/{profile_type}/{formatted_profile_type}-profiles.xml"
    )
    # API uses 'virus', antivirus just makes more sense. This switches it back for the API)
    api_profile_type = formatted_profile_type.replace("antivirus", "virus")

    # Export xml via Palo Alto API
    response = obj.get_request_pa(call_type="config", action="show", xpath=xpath)

    # Print out result
    result = xmltodict.parse(response)
    if result["response"]["@status"] == "success":

        # Check if one specific was searched or the entire list
        entry = result.get("response").get("result").get("entry")
        entries = result.get("response").get("result").get(api_profile_type)

        if entry:
            # Set filename to entry name
            object_name = result["response"]["result"]["entry"]["@name"]
            filename = f"{destination_folder}/{profile_type}/{object_name}.xml"
            # Add root tags (i.e. <spyware>), for clarity.
            # API doesn't return these tags on entry-specific requests
            temp = result["response"]["result"]
            data = {api_profile_type: temp}
            # Create file
            write_data_output(data, filename)
            print(f"\nExported {profile_type} object.")
        elif entries:
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
            write_data_output(result, filename)
            print(f"Output also written to {filename}")
        else:
            print(f"\nError exporting {profile_type} object.")
            print(
                "(Normally this just means no object found, set DEBUG=True if needed)"
            )


# Main Program
def main(profile_list, root_folder, selection, entry):

    # Organize user input
    # Expand '1' to '2,3,4,5,6,7,8,9,A'
    if "1" in profile_list:
        profile_list = [str(x) for x in range(2, 10)]
        profile_list.append("A")
    # Expand '2-5,8-9' to '2,3,4,5,8,9'
    if "-" in profile_list:
        dashes = [index for index, value in enumerate(profile_list) if value == "-"]
        remaining = profile_list
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
            profile_list = final + remaining
        else:
            profile_list = final

    # 1 = Export, 2 = Import
    if selection == "1":
        wrapper_call = export_profile_objects
    else:
        wrapper_call = import_profile_objects

    # Loop through user provided input, import each profile
    for profile in profile_list:
        if profile == "2":
            wrapper_call(root_folder, "antivirus", ANTIVIRUS + entry)
        elif profile == "3":
            wrapper_call(root_folder, "custom/spyware", SPYWARESIG + entry)
            wrapper_call(root_folder, "spyware", SPYWARE + entry)
        elif profile == "4":
            wrapper_call(root_folder, "custom/vulnerability", VULNERABLESIG + entry)
            wrapper_call(root_folder, "vulnerability", VULNERABILITY + entry)
        elif profile == "5":
            wrapper_call(root_folder, "custom/custom-url-category", URLCATEGORY + entry)
            wrapper_call(root_folder, "url-filtering", URLFILTERING + entry)
        elif profile == "6":
            wrapper_call(root_folder, "file-blocking", FILEBLOCKING + entry)
        elif profile == "7":
            wrapper_call(root_folder, "wildfire-analysis", WILDFIRE + entry)
        elif profile == "8":
            wrapper_call(root_folder, "custom/data-objects", DATAPATTERN + entry)
            wrapper_call(root_folder, "data-filtering", DATAFILTERING + entry)
        elif profile == "9":
            wrapper_call(root_folder, "dos-protection", DDOS + entry)
        elif profile == "A" or profile == "a":
            wrapper_call(root_folder, "profile-group", PROFILEGROUP + entry)
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
    obj = pa.xml_api_lib_pa(pa_ip, username, password)

    # MENU
    export_or_import = ""
    while export_or_import != "1" and export_or_import != "2":
        export_or_import = input(
            """\nWhat would you like to do?

        1) EXPORT security-profile objects (From PA into xml)
        2) IMPORT security-profile objects (From xml into PA)

        Enter 1 or 2: """
        )

    allowed = list("123456789aA-,")  # Allowed user input
    incorrect_input = True
    while incorrect_input:
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

            A) Profile Object Groups

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

    if len(selection) == 1 and selection != "1":
        entry = input(
            """\n
            (Blank line for all objects)
            Enter a specific object name: """
        )
        # Check if a specific object was requested
        if entry:
            entry = f"/entry[@name='{entry}']"
    else:
        entry = ""

    # Turn input into list, remove commas
    profile_list = list(selection.replace(",", ""))

    # Run program
    main(profile_list, root_folder, export_or_import, entry)

    # Done!
    print("\n\nComplete!\n")
