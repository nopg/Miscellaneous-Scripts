"""
Class with REST Api GET and POST libraries

Example: python rest_api_lib.py vmanage_hostname username password

PARAMETERS:
    vmanage_hostname : Ip address of the vmanage or the dns name of the vmanage
    username : Username to login the vmanage
    password : Password to login the vmanage

Note: All three arguments are manadatory
"""
import requests
import sys
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class rest_api_lib:
    def __init__(self, vmanage_ip, username, password):
        self.vmanage_ip = vmanage_ip
        self.session = {}
        self.login(self.vmanage_ip, username, password)

    def login(self, vmanage_ip, username, password):
        """Login to vmanage"""
        base_url_str = 'https://{}/'.format(vmanage_ip)

        login_action = '/j_security_check'

        #Format data for loginForm
        login_data = {'j_username' : username, 'j_password' : password}

        #Url for posting login data
        login_url = base_url_str + login_action

        url = base_url_str + login_url

        sess = requests.session()

        #If the vmanage has a certificate signed by a trusted authority change verify to True
        login_response = sess.post(url=login_url, data=login_data, verify=False)

        if b'<html>' in login_response.content:
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

    def post_request(self, mount_point, payload, headers={'Content-Type': 'application/json'}):
        """POST request"""
        url = "https://{}:443/dataservice/{}".format(self.vmanage_ip, mount_point)
        payload = json.dumps(payload)
        response = self.session[self.vmanage_ip].post(url=url, data=payload, headers=headers, verify=False)
        data = response.content
        
def main(args):
    if not len(args) == 2:
        print (__doc__)
        return
    vmanage_ip, username = args[0], args[1]
    password = input("Enter Password: ")
    obj = rest_api_lib(vmanage_ip, username, password)

    ## OUTPUT ALL FEATURE TEMPLATES
    response = obj.get_request('template/feature')
    
    json_response = json.loads(response)
    data = json_response["data"]

    for each in data:
        if not each["factoryDefault"]:
            fout = open("output/feature/" + each["templateName"], 'w')
            test = json.dumps(each)
            fout.write(test)
            fout.close()

    ## GET ALL DEVICE TEMPLATES
    response = obj.get_request('template/device')
    
    json_response = json.loads(response)
    data = json_response["data"]

    for each in data:
        templateId = each["templateId"]
        template = obj.get_request('template/device/object/' + templateId)
        template_json = json.loads(template)

        fout = open("output/device/" + template_json["templateName"], 'w')
        test = json.dumps(template_json)
        fout.write(test)
        fout.close()

    ## OUTPUT ALL DEVICE TEMPLATES

    #print(json_response.data)

    #Example request to make a Post call to the vmanage "url=https://vmanage.viptela.com/dataservice/device/action/rediscover"
    #payload = {"action":"rediscover","devices":[{"deviceIP":"172.16.248.105"},{"deviceIP":"172.16.248.106"}]}
    #response = obj.post_request('device/action/rediscover', payload)
    #print response

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))