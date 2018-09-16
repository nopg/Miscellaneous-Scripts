import requests
import getpass
import sys
import xmltodict, json
import xml.etree.ElementTree as etree
import io
import os

from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

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

class rest_api_lib_pa:
    def __init__(self, pa_ip, username, password):
        self.pa_ip = pa_ip
        self.session = {}
        self.key = 0
        self.login(self.pa_ip, username, password)

    def login(self, pa_ip, username, password):
        """Login to vmanage"""
        base_url_str = "https://{}/".format(pa_ip)

        login_action = "/api?type=keygen"

        # Format data for loginForm
        login_data = "&user={}&password={}".format(username,password)

        # Url for posting login data
        login_url = base_url_str + login_action + login_data

        sess = requests.session()

        # If the vmanage has a certificate signed by a trusted authority change verify to True
        login_response = sess.post(url=login_url, verify=False)

        if login_response.status_code == 403:
            print("Login Failed")
            sys.exit(0)

        self.session[pa_ip] = sess
        temp = xmltodict.parse(login_response.text)
        self.key = temp["response"]["result"]["key"]

    def get_request_pa(self, type="config", action="show", xpath=None, element=None):
        """GET request"""

        if not element:
            url = f"https://{self.pa_ip}:443/api?type={type}&action={action}&xpath={xpath}&key={self.key}"
        else:
            url = f"https://{self.pa_ip}:443/api?type={type}&action={action}&xpath={xpath}&key={self.key}&element={element}"
        if DEBUG:
            print(url)
        response = self.session[self.pa_ip].get(url, verify=False)
        data = etree.fromstring(response.text)
        return data


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
            print("\nOnly option 2, 3, 4, 5, 6, 7, and 8 are currently supported.\n")
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

    obj = rest_api_lib_pa(pa_ip, username, password)


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
