"""
Description: 
    XML API Library to be used with the Palo Alto API

Requires:
    requests
    xmltodict
    json
        to install try: pip3 install xmltodict requests json

Author:
    Ryan Gillespie rgillespie@compunet.biz
    Docstring stolen from Devin Callaway

Tested:
    Tested on macos 10.12.3
    Python: 3.6.2
    PA VM100

Example usage:
        import xml_api_lib_pa as pa
        # export example:
        obj = pa.get_xml_request_pa(call_type="config",action="show",xpath="")
        # import example:
        obj = pa.get_xml_request_pa(call_type="config",action="set",xpath="..",element="<../>")

Cautions:
    Future abilities will be added when use-cases warrant,
     currently ONLY supported for export/import operations (type=config,action=show, get, or set)

Legal:
    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
    WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
    MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
    ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
    WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
    ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
    OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
"""

import requests
import sys
import os
import json
import xmltodict
import xml.dom.minidom
from datetime import datetime

# Who cares about SSL?
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

DEBUG = False

# XML API Class for use with Palo Alto API
class api_lib_pa:
    # Upon creation:
    def __init__(self, pa_ip, username, password):
        self.pa_ip = pa_ip
        self.session = {}
        self.key = 0
        self.login(self.pa_ip, username, password)

    # Called from init(), login to the Palo Alto
    def login(self, pa_ip, username, password):

        # Create URL's
        base_url_str = f"https://{pa_ip}/"  # Base URL
        login_action = "/api?type=keygen"  # Get API Key
        login_data = f"&user={username}&password={password}"  # Format data for login
        login_url = (
            base_url_str + login_action + login_data
        )  # URL for posting login data

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
        self.key = temp.get("response").get("result").get("key")
        if not self.key:
            print(f"Login Failed: Response=\n{temp}")
            sys.exit(0)

        # Create file for each profile type

    def create_xml_files(self, temp, filename):

        # Pull folder name from string
        end = filename.rfind("/")
        folder = filename[0:end]

        timestamp = "/" + \
        str(datetime.now().year) + '-' + \
        str(datetime.now().month) + '-' + \
        str(datetime.now().day) + '--' + \
        str(datetime.now().hour) + '-' + \
        str(datetime.now().minute) + '/'

        filename = folder + timestamp + filename[end:]

        # Create the root folder and subfolder if it doesn't already exist
        os.makedirs(folder + timestamp, exist_ok=True)


        # Because XML: remove <response/><result/> and <?xml> tags
        # Using get().get() won't cause exception on KeyError
        # Check for various response type and ensure xml is written consistently

        #Set data
        if not isinstance(temp,list):
            data = temp.get("response")
            data = {"response": data}

            if data:
                # data = temp.get("response").get("result")
                if data:
                    data = xmltodict.unparse(data)
                else:
                    data = xmltodict.unparse(temp)
            else:
                data = xmltodict.unparse(temp)
            data = data.replace('<?xml version="1.0" encoding="utf-8"?>', "")

            prettyxml = xml.dom.minidom.parseString(data).toprettyxml()

            with open(filename, "w") as fout:
                fout.write(prettyxml)
        else:
            data = temp
            with open(filename, "w") as fout:
                fout.write("\n".join(data))


    def create_json_files(self, temp, filename):
        """
        CREATE OUTPUT FILES 

        :param data: list of data to be written
        :param template_type: 'feature' or 'device'
        :return: None, print output
        """
        # Pull folder name from string
        end = filename.rfind("/")
        folder = filename[0:end]

        timestamp = "/" + \
        str(datetime.now().year) + '-' + \
        str(datetime.now().month) + '-' + \
        str(datetime.now().day) + '--' + \
        str(datetime.now().hour) + '-' + \
        str(datetime.now().minute) + '/'

        filename = folder + timestamp + filename[end:]

        # Create the root folder and subfolder if it doesn't already exist
        os.makedirs(folder + timestamp, exist_ok=True)

        data = json.dumps(temp, indent=4, sort_keys=True)
        # Write Data
        fout = open(filename, "w")
        fout.write(data)
        fout.close()

        # print("\tCreated: {}\n".format(filename))

    # GET request for Palo Alto API
    def get_xml_request_pa(
        self, call_type="config", action="show", xpath=None, element=None
    ):
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
            print(
                f"\nGET request sent: type={call_type}, action={action}, \n  xpath={xpath}.\n"
            )
            print(f"\nResponse Status Code = {response.status_code}")
            print(f"\nResponse = {response.text}")

        # Return string (XML)
        return response.text

    # GET request for Palo Alto API
    def get_rest_request_pa(self, restcall=None, element=None):
        headers = {"X-PAN-KEY": self.key}

        # If no element is sent, should be a 'show' or 'get' action, do not send &element=<element>
        if not element:
            url = f"https://{self.pa_ip}:443{restcall}"
        else:
            url = f"https://{self.pa_ip}:443{restcall}&element={element}"

        # Make the API call
        response = self.session[self.pa_ip].get(url, headers=headers, verify=False)

        # Extra logging if debugging
        if DEBUG:
            print(f"URL = {url}")
            print(f"\nGET request sent: restcall={restcall}.\n")
            print(f"\nResponse Status Code = {response.status_code}")
            print(f"\nResponse = {response.text}")

        # Return string (XML)
        return response.text

    def grab_api_output(
        self, xml_or_rest, xpath_or_restcall, filename=None,
    ):
        # Grab PA/Panorama API Output
        success = False
        if xml_or_rest == "xml":

            response = self.get_xml_request_pa(
                call_type="config", action="get", xpath=xpath_or_restcall
            )
            xml_response = xmltodict.parse(response)

            if xml_response["response"]["@status"] == "success":
                success = True

            if filename:
                self.create_xml_files(xml_response, filename)

            if not xml_response["response"]["result"]:
                print("Nothing found on PA/Panorama, are you connecting to the right device?")
                print(f"Check {filename} for XML API reply")
                sys.exit(0)

        elif xml_or_rest == "rest":

            response = self.get_rest_request_pa(restcall=xpath_or_restcall)
            json_response = json.loads(response)
            if json_response["@status"] == "success":
                success = True
            if filename:
                self.create_json_files(json_response, filename)

            if not json_response["result"]:
                print("Nothing found on PA/Panorama, are you connecting to the right device?")
                print(f"Check {filename} for XML API reply")

        if not success:
            # Extra logging when debugging
            if DEBUG:
                print(f"\nGET request sent: xpath={xpath_or_restcall}.\n")
                print(f"\nResponse: \n{response}")
                self.create_xml_files(response, filename)
                print(f"Output also written to {filename}")
            else:
                print(f"\nError exporting '{filename}' object.")
                print(
                    "(Normally this just means no object found, set DEBUG=True if needed)"
                )

        if xml_or_rest == "xml":
            return xml_response
        else:
            return json_response
