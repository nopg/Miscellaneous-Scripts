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
        if response.status_code == 200:
            return response.content
        else:
            print("\nERROR sending Post request: \n")
            print(url)
            print("Error: " + str(response.status_code))
            print(response.content)
            sys.exit(0)


def grab_files_read(folder_name):
    device_templates = []
    for root, dirs, files in os.walk(folder_name):
        for file in files:
            if file.endswith(".vipt"):
                with open(root + file, "r") as fin:
                    data = fin.read()
                    device_templates.append(data)
    return device_templates


def find_feature_template(old_id, feature_templates):

    # SEARCH THROUGH TEMPLATES #
    for template in feature_templates:
        data = json.loads(template)
        if data["templateId"] == old_id:
            data["factoryDefault"] = False
            if "Factory_Default_" in data["templateName"]:
                data["templateName"] = "Imported_" + data["templateName"]
            # CREATE NEW TEMPLATE #
            response = obj.post_request("template/feature", data)
            print("\tImported feature template: {}".format(data["templateName"]))
            new_id = json.loads(response)["templateId"]
            return new_id

    # TEMPLATE NOT FOUND! #
    print("\nRequired feature template not found! ID: {}".format(old_id))
    print("Exiting...\n")
    sys.exit(0)


def main(obj, root_folder):

    # GRAB TEMPLATES, creates list containing output of each file #
    device_templates = grab_files_read(root_folder + "/device/")
    feature_templates = grab_files_read(root_folder + "/feature/")

    for template in device_templates:
        data = json.loads(template)
        data["policyId"] = ""  #   ATTACHED TO ROUTING POLICY?
        data["factoryDefault"] = ""  #   NEVER A DEFAULT
        if data["configType"] == "template":  #   NOT A CLI BASED TEMPLATE
            # UPDATE OLD FEATURE TEMPLATE ID'S #
            for feature_template in data["generalTemplates"]:
                if "subTemplates" in feature_template:
                    for sub_template in feature_template["subTemplates"]:
                        old_feat_id = sub_template["templateId"]
                        # FIND FEATURE TEMPLATE AND CREATE NEW ONE #
                        new_id = find_feature_template(old_feat_id, feature_templates)
                        sub_template["templateId"] = new_id

                old_feat_id = feature_template["templateId"]
                # FIND FEATURE TEMPLATE AND CREATE NEW ONE #
                new_id = find_feature_template(old_feat_id, feature_templates)
                feature_template["templateId"] = new_id

        # CREATE DEVICE TEMPLATE
        response = obj.post_request("template/device/feature", data)
        print("Imported device template: {}\n".format(data["templateName"]))


if __name__ == "__main__":

    if len(sys.argv) != 4:
        print("\nplease provide the following arguments:")
        print(
            "\tpython3 put-templates.py <root template folder> <destination vmanage> <username>\n\n"
        )
        sys.exit(0)

    root_folder = sys.argv[1]
    dest_vmanage_ip = sys.argv[2]
    username = sys.argv[3]
    password = getpass.getpass("Enter Password: ")

    obj = rest_api_lib(dest_vmanage_ip, username, password)
    main(obj, root_folder)

    print("\n\nComplete!\n")
