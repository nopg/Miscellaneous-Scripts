import getpass
import sys
import os
import xml.etree.ElementTree as etree
from requests.packages.urllib3.exceptions import InsecureRequestWarning

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


def write_etree_output(profile, prof_type, destination_folder):

    #GRAB FILENAME FROM FIRST ENTRY?
    if prof_type == 'virus':
        filename = destination_folder + "/antivirus-profiles.xml"
    else:
        filename = destination_folder + "/" + prof_type + "-profiles.xml"
            
    data = etree.tostring(profile[0][0]).decode()
    with open (filename, "w") as fout:
        fout.write(data)

def find_profile_objects(destination_folder, prof_type):
    
    new_destination = destination_folder + "/" + prof_type

    if prof_type == 'virus':
        xpath = ANTIVIRUS
        new_destination = destination_folder + "/antivirus"
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

    os.makedirs(new_destination, exist_ok=True)

    profile_objects = obj.get_request_pa(type='config',action='show',xpath=xpath)
    # if DEBUG:
    #     for elem in profile_objects.iter():
    #         print(elem)
    #         print(elem.attrib)
    #         print(elem.text)

    write_etree_output(profile_objects, prof_type, new_destination)

def main(profile_list, destination_folder):

    if '1' in profile_list:
        profile_list = [str(x) for x in range(2,10)]

    if '-' in profile_list:
        start = int (profile_list[0])
        end = profile_list[-1:]
        end = int (end[0]) + 1
        profile_list = [str(x) for x in range(start,end)]

    for profile in profile_list:

        if profile == '2':
            find_profile_objects(destination_folder, 'virus')
        elif profile == '3':
            find_profile_objects(destination_folder, 'spyware')
        elif profile == '4':
            find_profile_objects(destination_folder,'vulnerability')
        elif profile == '5':
            find_profile_objects(destination_folder,'url-filtering')
        elif profile == '6':
            find_profile_objects(destination_folder,'file-blocking')
        elif profile == '7':
            find_profile_objects(destination_folder,'wildfire-analysis')
        elif profile == '8':
            find_profile_objects(destination_folder,'data-filtering')
        elif profile == '9':
            find_profile_objects(destination_folder,'dos-protection')
        else:
            print("\nHuh?. You entered {}\n".format(profile))
            continue


if __name__ == "__main__":

    if len(sys.argv) != 4:
        print("\nplease provide the following arguments:")
        print(
            "\tpython3 dh-security-profiles.py <destination folder> <PA mgmt IP> <username>\n\n"
        )
        sys.exit(0)

    destination_folder = sys.argv[1]
    pa_ip = sys.argv[2]
    username = sys.argv[3]
    password = getpass.getpass("Enter Password: ")

    obj = pa.rest_api_lib_pa(pa_ip, username, password)


    selection = input("""\nWhat type of security profiles to export?

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
    
    main(profile_list, destination_folder)

    print("\n\nComplete!\n")
