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
            print("\nHUH?.\n")
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

    obj = rest_api_lib_pa(pa_ip, username, password)


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

