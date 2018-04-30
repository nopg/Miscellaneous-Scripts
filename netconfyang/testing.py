"""
    Netconf python example by yang-explorer (https://github.com/CiscoDevNet/yang-explorer)

    Installing python dependencies:
    > pip install lxml ncclient

    Running script: (save as example.py)
    > python example.py -a 10.101.255.10 -u admin -p 4N@LHEH5VkZGpC --port 830
"""

import lxml.etree as ET
from argparse import ArgumentParser
from ncclient import manager
from ncclient.operations import RPCError
import xml.dom.minidom

interface_state = """
<filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces-state xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
      <admin-status/>
    </interface>
  </interfaces-state>
</filter>
"""

interface_speed = """
<filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces-state xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
      <speed/>
    </interface>
  </interfaces-state>
</filter>
"""

interface_name= """
<filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces-state xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
      <name/>
    </interface>
  </interfaces-state>
</filter>
"""

interface_description= """
<filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
      <description/>
    </interface>
  </interfaces>
</filter>
"""

payload = interface_name



if __name__ == '__main__':

    parser = ArgumentParser(description='Usage:')

    # script arguments
    parser.add_argument('-a', '--host', type=str, required=True,
                        help="Device IP address or Hostname")
    parser.add_argument('-u', '--username', type=str, required=True,
                        help="Device Username (netconf agent username)")
    parser.add_argument('-p', '--password', type=str, required=True,
                        help="Device Password (netconf agent password)")
    parser.add_argument('--port', type=int, default=830,
                        help="Netconf agent port")
    args = parser.parse_args()

    # connect to netconf agent
    with manager.connect(host=args.host,
                         port=args.port,
                         username=args.username,
                         password=args.password,
                         timeout=90,
                         hostkey_verify=False,
                         device_params={'name': 'default'}) as m:

        # execute netconf operation
        try:
            response = m.get(payload)
            #data = ET.fromstring(response)
        except RPCError as e:
            data = e._raw

        # beautify output
        #print(ET.tostring(data, pretty_print=True))

        xml_doc = xml.dom.minidom.parseString(response.xml)
        description = xml_doc.getElementsByTagName("name")

        for item in description:
          print(item.firstChild.nodeValue)
        
        #print(description[0].firstChild.nodeValue) 

