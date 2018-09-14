"""
Class with REST Api GET and POST libraries

Example: python3 get-templates.py vmanage_hostname username

PARAMETERS:
    vmanage_hostname : Ip address of the vmanage or the dns name of the vmanage
    username : Username to login the vmanage

Note: All three arguments are manadatory
"""
import requests
import sys
import os
import json
import getpass
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def pp_json(json_thing, sort=True, indents=4):
    """
    PRETTY PRINT JSON WHETHER STRING OR DICTIONARY

    :param json_thing: object to be printed
    :return: None, print output
    """
    if type(json_thing) is str:
        print("STR")
        print(json.dumps(json.loads(json_thing), sort_keys=sort, indent=indents))
    else:
        print(json.dumps(json_thing, sort_keys=sort, indent=indents))
    return None


class rest_api_lib:
    def __init__(self, vmanage_ip, username, password):
        self.vmanage_ip = vmanage_ip
        self.session = {}
        self.login(self.vmanage_ip, username, password)

    def login(self, vmanage_ip, username, password):
        """Login to vmanage"""
        base_url_str = "https://{}/".format(vmanage_ip)

        login_action = "/j_security_check"

        # Format data for loginForm
        login_data = {"j_username": username, "j_password": password}

        # Url for posting login data
        login_url = base_url_str + login_action

        url = base_url_str + login_url

        sess = requests.session()

        # If the vmanage has a certificate signed by a trusted authority change verify to True
        login_response = sess.post(url=login_url, data=login_data, verify=False)

        if b"<html>" in login_response.content:
            print("Login Failed")
            sys.exit(0)

        self.session[vmanage_ip] = sess

    def get_request(self, mount_point):
        """GET request"""
        url = "https://{}:443/dataservice/{}".format(self.vmanage_ip, mount_point)
        print(url)
        response = self.session[self.vmanage_ip].get(url, verify=False)
        data = response.content
        return data

    def post_request(
        self, mount_point, payload, headers={"Content-Type": "application/json"}
    ):
        """POST request"""
        url = "https://{}:443/dataservice/{}".format(self.vmanage_ip, mount_point)
        payload = json.dumps(payload)
        response = self.session[self.vmanage_ip].post(
            url=url, data=payload, headers=headers, verify=False
        )
        print(response)
        data = response.content
        return data


def grab_files_read(folder_name):
    """
    GRAB ALL FILES WITH ".vipt" EXTENSION WITHIN A FOLDER,
    RETURN LIST CONTAINING TEXT FOUND WITHIN FILES

    :param folder_name: base folder to recursively search
    :return: list containing the output of each folder
    """
    templates = []
    for root, dirs, files in os.walk(folder_name):
        for file in files:
            if file.endswith(".vipt"):
                with open(root + file, "r") as fin:
                    data = fin.read()
                    templates.append(data)
    return templates


def create_files(data, subfolder):
    """
    CREATE OUTPUT FILES BY FIRST RETRIEVING EACH OBJECT (FEATURE OR TEMPLATE)
    Based on 'subfolder' will pull individal 'device' or 'feature' templates
    and output them to a file

    :param data: list of data to be written
    :param subfolder: 'feature' or 'device'
    :return: None, print output
    """
    subfolder = "/" + subfolder + "/"
    for each in data:
        # if not each["factoryDefault"]:
        response = obj.get_request(
            "template" + subfolder + "object/" + each["templateId"]
        )
        template = json.loads(response)
        filename = template["templateName"].replace(os.path.sep, "_") + ".vipt"
        fout = open(root_folder + subfolder + filename, "w")
        fout.write(json.dumps(template))
        fout.close()


def main(obj, root_folder):

    os.makedirs(root_folder + "/device", exist_ok=True)
    os.makedirs(root_folder + "/feature", exist_ok=True)

    ## OUTPUT ALL FEATURE TEMPLATES
    response = obj.get_request("template/feature")
    json_response = json.loads(response)

    feature_data = json_response["data"]
    create_files(feature_data, "feature")

    ## GET ALL DEVICE TEMPLATES
    response = obj.get_request("template/device")
    json_response = json.loads(response)

    device_data = json_response["data"]
    create_files(device_data, "device")


if __name__ == "__main__":

    if len(sys.argv) != 4:
        print("\nplease provide the following arguments:")
        print(
            "\tpython3 put-templates.py <output template folder> <destination vmanage> <username>\n\n"
        )
        sys.exit(0)

    root_folder = sys.argv[1]
    dest_vmanage_ip = sys.argv[2]
    username = sys.argv[3]
    password = getpass.getpass("Enter Password: ")

    obj = rest_api_lib(dest_vmanage_ip, username, password)
    main(obj, root_folder)

    print("\n\nComplete!\n")
