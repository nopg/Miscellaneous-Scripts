import getpass
import sys
import os
import xml.etree.ElementTree as etree

import rest_api_lib_pa as pa

# Global Variables, debug & xpath location for each profile type
#ENTRY = + "/entry[@name='alert-only']"
DEBUG = False
ANTIVIRUS =     "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/virus"
SPYWARE =       "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/spyware"
VULNERABILITY = "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/vulnerability"
URLFILTERING =  "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/url-filtering"
FILEBLOCKING =  "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/file-blocking"
WILDFIRE =      "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/wildfire-analysis"
DATAFILTERING = "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/data-filtering"
DATAPATTERN =   "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/data-objects"
DDOS =          "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/dos-protection"


# Read all files found in folder_name, return list containing all the output
def grab_files_read(folder_name):
    profile_objects = []
    for root, dirs, files in os.walk(folder_name):
        for file in files:
            if file.endswith(".xml"):
                with open(root + "/" + file, "r") as fin:
                    data = fin.read()
                    profile_objects.append(data)
    return profile_objects

# Imports profiles into Palo Alto API based on profile type
def import_profile_objects(root_folder, profile_type, xpath):

    # Rename 'virus' folder to 'antivirus' (just makes more sense)
    if profile_type == 'virus':
        new_root = root_folder + "/antivirus"
    else:
        new_root = root_folder + "/" + profile_type
    
    if profile_type == 'data-filtering':
        import_profile_objects(root_folder, 'data-objects', DATAPATTERN)

    # Gather all files, returns string containing xml
    files = grab_files_read(new_root)

    # because: xml.
    # create root tags (i.e. <virus>, </spyware>, etc)
    root_tag = "<" + profile_type + ">"
    root_tag_end = "</" + profile_type + ">"

    for xml in files:        
        # because: xml.
        # remove root tag (i.e. <virus>, </spyware>, etc)
        entry_element = xml.replace(root_tag,"")
        entry_element = entry_element.replace(root_tag_end,"")
        
        # Import xml via Palo Alto API
        response = obj.get_request_pa(call_type="config",action="set",xpath=xpath,element=entry_element)
    
        #Print out result
        result = response.attrib

        if result["status"] == 'success':
            print(f"\nImported {profile_type} object.")
        else:
            # Extra logging when debugging
            if DEBUG:
                print(f"\nGET request sent: xpath={xpath}.\n element={entry_element}\n")
                string_response = etree.tostring(response).decode()
                print(string_response)
            else:
                print(f"\nError importing {profile_type} object.")

# Main Program
def main(profile_list, root_folder):

    # Organize user input
    # Expand '1' to '2,3,4,5,6,7,8,9'
    if '1' in profile_list:
        profile_list = [str(x) for x in range(2,10)]
    # Expand '2-5' to '2,3,4,5'
    if '-' in profile_list:
        start = int (profile_list[0])
        end = profile_list[-1:]
        end = int (end[0]) + 1
        profile_list = [str(x) for x in range(start,end)]

    # Loop through user provided input, import each profile
    for profile in profile_list:
        if profile == '2':
            import_profile_objects(root_folder,'virus', ANTIVIRUS)
        elif profile == '3':
            import_profile_objects(root_folder,'spyware', SPYWARE)
        elif profile == '4':
            import_profile_objects(root_folder,'vulnerability', VULNERABILITY)
        elif profile == '5':
            import_profile_objects(root_folder,'url-filtering', URLFILTERING)
        elif profile == '6':
            import_profile_objects(root_folder,'file-blocking', FILEBLOCKING)
        elif profile == '7':
            import_profile_objects(root_folder,'wildfire-analysis', WILDFIRE)
        elif profile == '8':
            import_profile_objects(root_folder,'data-filtering', DATAFILTERING)
        elif profile == '9':
            import_profile_objects(root_folder,'dos-protection', DDOS)
        else:
            print("\nHuh?. You entered {}\n".format(profile))
            continue

# If run from the command line
if __name__ == "__main__":

    # Guidance on how to use the script
    if len(sys.argv) != 4:
        print("\nplease provide the following arguments:")
        print(
            "\tpython3 dh-security-profiles.py <root folder for profiles> <PA mgmt IP> <username>\n\n"
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
    selection = input("""\nWhat type of security profiles to import?

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

                Enter Selection: """)

    # Turn input into list, remove commas
    profile_list = list(selection.replace(',',''))
    
    # Run program
    main(profile_list, root_folder)

    # Done!
    print("\n\nComplete!\n")

