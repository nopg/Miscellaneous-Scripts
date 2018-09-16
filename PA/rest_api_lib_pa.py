import requests
import sys
import xml.etree.ElementTree as etree

import xmltodict

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

DEBUG = False

# REST API Class for use with Palo Alto API
class rest_api_lib_pa:
    # Upon creation:
    def __init__(self, pa_ip, username, password):
        self.pa_ip = pa_ip
        self.session = {}
        self.key = 0
        self.login(self.pa_ip, username, password)

    # Called from init, login to the Palo Alto
    def login(self, pa_ip, username, password):
        """ Called from init, login to the Palo Alto"""

        # Create URL's
        base_url_str = "https://{}/".format(pa_ip)                      # Base URL
        login_action = "/api?type=keygen"                               # Get API Key
        login_data = "&user={}&password={}".format(username,password)   # Format data for login 
        login_url = base_url_str + login_action + login_data            # URL for posting login data

        # Create requests session
        sess = requests.session()

        # get API key
        login_response = sess.post(url=login_url, verify=False)

        # Login Failed check
        if login_response.status_code == 403:
            print("Login Failed")
            sys.exit(0)

        # Set successful session and key
        self.session[pa_ip] = sess
        temp = xmltodict.parse(login_response.text)
        self.key = temp["response"]["result"]["key"]

    # GET request for Palo Alto API
    def get_request_pa(self, call_type="config", action="show", xpath=None, element=None):
        """ GET request for Palo Alto API """

        # If no element is sent, should be a 'show' or 'get' action, do not send &element=<element>
        if not element:
            url = f"https://{self.pa_ip}:443/api?type={call_type}&action={action}&xpath={xpath}&key={self.key}"
        else:
            url = f"https://{self.pa_ip}:443/api?type={call_type}&action={action}&xpath={xpath}&key={self.key}&element={element}"
        
        # Make the API call
        response = self.session[self.pa_ip].get(url, verify=False)

        # Extra logging if debugging
        if DEBUG:
            print(f"URL = {url}")
            print(f"\nGET request sent: type={call_type}, action={action}, \n  xpath={xpath}.\n")
            

        # Turn into ElementTree (XML) and return
        data = etree.fromstring(response.text)
        return data
