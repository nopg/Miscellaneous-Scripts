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
ANTIVIRUS = "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/virus"
SPYWARE =   "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/spyware"
VULNERABILITY = "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/vulnerability"

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

    # def get_request_pa_cli(self, mount_point, commands):
    #     """GET request"""

    #     command_list = commands.split()
        
    #     params = []
    #     for command in command_list:
    #         params.append("<" + command + ">")
    #     for command in command_list[::-1]:
    #         params.append("</" + command + ">")
        
    #     command = ''.join(params)

    #     url = "https://{}:443/api{}{}&key={}".format(self.pa_ip, mount_point, command, self.key)
    #     print(url)
    #     response = self.session[self.pa_ip].get(url, verify=False)
    #     data = response.text
    #     return data

    # def get_request_pa_cli_and_param(self, mount_point, commands):
    #     """GET request"""

    #     command_list = commands.split()
    #     value = command_list.pop()
    #     params = []

    #     for command in command_list:
    #         params.append("<" + command + ">")
    #     params.append(value)

    #     for command in command_list[::-1]:
    #         params.append("</" + command + ">")
        
    #     command = ''.join(params)

    #     url = "https://{}:443/api{}{}&key={}".format(self.pa_ip, mount_point, command, self.key)
    #     print(url)
    #     response = self.session[self.pa_ip].get(url, verify=False)
    #     data = response.text
    #     return data

    # def post_request(
    #     self, mount_point, payload, headers={"Content-Type": "application/json"}
    # ):
    #     """POST request"""
    #     url = "https://{}:443/dataservice/{}".format(self.vmanage_ip, mount_point)
    #     payload = json.dumps(payload)
    #     response = self.session[self.vmanage_ip].post(
    #         url=url, data=payload, headers=headers, verify=False
    #     )
    #     print(response)
    #     data = response.text
    #     return data

# def write_etree_output(profile, type):

#     #GRAB FILENAME
#     if type == 'virus':
#         data = etree.tostring(profile[0][0]).decode()
#         with open ("Antivirus-profiles.xml", "w") as fout:
#             fout.write(data)

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
    pass

def main(profile_list, root_folder):

    for profile in profile_list:
        if profile == '2':
            xpath = ANTIVIRUS 
            os.makedirs(root_folder + "/antivirus", exist_ok=True) 
            new_root = root_folder + "/antivirus"
            files = grab_files_read(new_root)

            for xml in files:
                
                # because: xml.
                temp = xmltodict.parse(xml)
                entry_element = xmltodict.unparse(temp)
                entry_element = entry_element.replace("<virus>","")
                entry_element = entry_element.replace("</virus>","")
                entry_element = entry_element.replace("<?xml version=\"1.0\" encoding=\"utf-8\"?>","")
                
                response = obj.get_request_pa(type="config",action="set",xpath=xpath,element=entry_element)
            
                if DEBUG:
                    for elem in response.iter():
                        print(elem)
                        print(elem.attrib)
                        print(elem.text)
        elif profile == '3':
            xpath = SPYWARE 
            os.makedirs(root_folder + "/spyware", exist_ok=True) 
            new_root = root_folder + "/spyware"
            files = grab_files_read(new_root)

            for xml in files:
                
                # because: xml.
                temp = xmltodict.parse(xml)
                entry_element = xmltodict.unparse(temp)
                entry_element = entry_element.replace("<spyware>","")
                entry_element = entry_element.replace("</spyware>","")
                entry_element = entry_element.replace("<?xml version=\"1.0\" encoding=\"utf-8\"?>","")
                
                response = obj.get_request_pa(type="config",action="set",xpath=xpath,element=entry_element)
            
                if DEBUG:
                    for elem in response.iter():
                        print(elem)
                        print(elem.attrib)
                        print(elem.text)
        else:
            print(profile)
            print("\nOnly option 2 and 3 is currently supported.\n")
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


    # tree = etree.parse(io.StringIO(av))
    # root = tree.getroot()
    #print(tree.getroot().text)
    #print(tree[0])
    #print(root.tag)

    #d = xmltodict.parse(av)
    #print(d)



    print("\n\nComplete!\n")


    # def pp_xml(text):
    #     b = xmltodict.parse(test)
    #     pp_json(b)

    #for elem in av_objects.iter():
    #    print(elem)
    # tree = etree.ElementTree(av_objects)
    # e = av_objects.findall(".//result/virus/entry")
    # for i in e:
    #     print(i)
    #     print(i.text)
    #     print(i.attrib)

