"""
Description: 
    XML API Library to be used with the Palo Alto API

Requires:
    requests
    xmltodict
        to install try: pip3 install xmltodict requests 

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
        obj = pa.get_request_pa(call_type="config",action="show",xpath="")
        # import example:
        obj = pa.get_request_pa(call_type="config",action="set",xpath="..",element="<../>")

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

import xmltodict

from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

DEBUG = False

# XML API Class for use with Palo Alto API
class xml_api_lib_pa:
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

    # GET request for Palo Alto API
    def get_request_pa(
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

        # Return string (XML)
        return response.text
