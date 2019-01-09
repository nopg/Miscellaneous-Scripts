import requests
import sys
import json

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

DEBUG = False

class rest_api_lib_meraki:
    def __init__(self, APIKEY):
        self.APIKEY = APIKEY
        self.session = {}
        self.login(self.APIKEY)

    def login(self, APIKEY):
        """Login to Meraki"""
        self.base_url_str = "https://api.meraki.com/api/v0/"

        # Format data for loginForm
        self.login_data = {"X-Cisco-Meraki-API-Key": self.APIKEY}

        # Url for posting login data
        login_url = self.base_url_str + "organizations"

        sess = requests.session()

        # If the vmanage has a certificate signed by a trusted authority change verify to True
        login_response = sess.get(url=login_url, headers=self.login_data, verify=False)

        if login_response.status_code != 200:
            print("Login Failed")
            if DEBUG:
                print(login_response)
                print(login_url)
                print(self.login_data)
            sys.exit(0)

        self.session[self.APIKEY] = sess

    def get_request(self, mount_point):
        """GET request"""
        url = self.base_url_str + mount_point
        if DEBUG:
            print(url)
        response = self.session[self.APIKEY].get(url, headers=self.login_data, verify=False)

        if response.status_code != 200:
            print("Error")
            if DEBUG:
                print(response)
                print(url)
                print(self.login_data)
            sys.exit(0)

        data = response.text
        return json.loads(data)

    def post_request(
        self, mount_point, payload
    ):
        """POST request"""
        url = self.base_url_str + mount_point
        payload = json.dumps(payload)
        headers = {"X-Cisco-Meraki-API-Key": self.APIKEY, "Content-Type": "application/json"}

        if DEBUG:
            print(url)

        response = self.session[self.APIKEY].post(
            url=url, data=payload, headers=headers, verify=False
        )
        if response.status_code == 201:
            return "Success"
        else:
            return response

