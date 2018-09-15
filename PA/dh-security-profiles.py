import requests
import getpass
import sys
import xmltodict, json
import xml.etree.ElementTree as etree
import io

from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

ANTIVIRUS = "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/profiles/virus"

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

def grab_objects():
    pass

if __name__ == "__main__":

    if len(sys.argv) != 3:
        print("\nplease provide the following arguments:")
        print(
            "\tpython3 dh-security-profiles.py <PA mgmt IP> <username>\n\n"
        )
        sys.exit(0)

    pa_ip = sys.argv[1]
    username = sys.argv[2]
    password = getpass.getpass("Enter Password: ")

    obj = rest_api_lib_pa(pa_ip, username, password)

    xpath = ANTIVIRUS #+ "/entry[@name='alert-only']"

    av_objects = obj.get_request_pa(type='config',action='show',xpath=xpath)

    with open("virus-alert-only.xml", "r") as fin:
         av = fin.read()

    entry_element = av

    tree = etree.parse(io.StringIO(av))
    print(tree.getroot().text)

    response = obj.get_request_pa(type="config",action="set",xpath=xpath,element=entry_element)

    # for elem in response.iter():
    #      print(elem)
    #      print(elem.attrib)
    #      print(elem.text)


    print("\n\nComplete!\n")


    #test = obj.get_request_pa_cli_and_param("?type=op&cmd=",command)

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

    # data = etree.tostring(av_objects[0][0]).decode()
    # with open ("xmltest.xml", "w") as fout:
    #     fout.write(data)