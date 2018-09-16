import getpass
import sys
import os
import xml.etree.ElementTree as etree

import xmltodict
import rest_api_lib_pa as pa

#ENTRY = + "/entry[@name='alert-only']"
DEBUG = True
ANTIVIRUS =     "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/virus"
SPYWARE =       "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/spyware"
VULNERABILITY = "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/vulnerability"
URLFILTERING =  "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/url-filtering"
FILEBLOCKING =  "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/file-blocking"
WILDFIRE =      "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/wildfire-analysis"
DATAFILTERING = "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/data-filtering"
DDOS =          "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/dos-protection"


def grab_files_read(folder_name):
    profile_objects = []
    for root, dirs, files in os.walk(folder_name):
        for file in files:
            if file.endswith(".xml"):
                with open(root + "/" + file, "r") as fin:
                    data = fin.read()
                    profile_objects.append(data)
    return profile_objects

def import_profile_objects(root_folder, prof_type):

    new_root = root_folder + "/" + prof_type

    if prof_type == 'virus':
        xpath = ANTIVIRUS
        new_root = root_folder + "/antivirus"
    elif prof_type == 'spyware':
        xpath = SPYWARE
    elif prof_type == 'vulnerability':
        xpath = VULNERABILITY
    elif prof_type == 'url-filtering':
        xpath = URLFILTERING
    elif prof_type == 'file-blocking':
        xpath = FILEBLOCKING
    elif prof_type == 'wildfire-analysis':
        xpath = WILDFIRE
    elif prof_type == 'data-filtering':
        xpath = DATAFILTERING
    elif prof_type == 'dos-protection':
        xpath = DDOS

    #os.makedirs(new_root, exist_ok=True) 
    files = grab_files_read(new_root)

    remove_root_tag = "<" + prof_type + ">"
    remove_root_tag_end = "</" + prof_type + ">"

    for xml in files:        
        # because: xml.
        temp = xmltodict.parse(xml)
        entry_element = xmltodict.unparse(temp)
        entry_element = entry_element.replace(remove_root_tag,"")
        entry_element = entry_element.replace(remove_root_tag_end,"")
        entry_element = entry_element.replace("<?xml version=\"1.0\" encoding=\"utf-8\"?>","")
        
        response = obj.get_request_pa(type="config",action="set",xpath=xpath,element=entry_element)
    
        if DEBUG:
            for elem in response.iter():
                print(elem)
                print(elem.attrib)
                print(elem.text)

def main(profile_list, root_folder):

    if '1' in profile_list:
        profile_list = [str(x) for x in range(2,10)]

    if '-' in profile_list:
        start = int (profile_list[0])
        end = profile_list[-1:]
        end = int (end[0]) + 1
        profile_list = [str(x) for x in range(start,end)]

    for profile in profile_list:
        if profile == '2':
            import_profile_objects(root_folder,'virus')
        elif profile == '3':
            import_profile_objects(root_folder,'spyware')
        elif profile == '4':
            import_profile_objects(root_folder,'vulnerability')
        elif profile == '5':
            import_profile_objects(root_folder,'url-filtering')
        elif profile == '6':
            import_profile_objects(root_folder,'file-blocking')
        elif profile == '7':
            import_profile_objects(root_folder,'wildfire-analysis')
        elif profile == '8':
            import_profile_objects(root_folder,'data-filtering')
        elif profile == '9':
            import_profile_objects(root_folder,'dos-protection')
        else:
            print("\nHuh?. You entered {}\n".format(profile))
            continue

if __name__ == "__main__":

    if len(sys.argv) != 4:
        print("\nplease provide the following arguments:")
        print(
            "\tpython3 dh-security-profiles.py <root folder for profiles> <PA mgmt IP> <username>\n\n"
        )
        sys.exit(0)

    root_folder = sys.argv[1]
    pa_ip = sys.argv[2]
    username = sys.argv[3]
    password = getpass.getpass("Enter Password: ")

    obj = pa.rest_api_lib_pa(pa_ip, username, password)


    selection = input("""\nWhat type of security profiles to import??

                1) ALL Profiles
                2) Antivirus
                3) Anti-Spyware
                4) Vulnerability Protection
                5) URL Filtering
                6) File Blocking
                7) Wildfire Analysis
                8) Data Filtering
                9) DoS Protection

                Separate selection by comma: """)
    profile_list = list(selection.replace(',',''))
    
    main(profile_list, root_folder)

    print("\n\nComplete!\n")

