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
import xmltodict

interface_state = """
<filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces-state xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
      <name/>
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
      <name/>
      <description/>
    </interface>
  </interfaces>
</filter>
"""

sample_reply = """
<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:be44a2ee-89ad-40e7-9533-f86a847c41cc" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <data>
    <interfaces-state xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
        <interface>
            <name>port1</name>
            <admin-status>down</admin-status>
        </interface>
        <interface>
            <name>port2</name>
            <admin-status>up</admin-status>
        </interface>
        <interface>
            <name>port3</name>
            <admin-status>down</admin-status>
        </interface>
        <interface>
            <name>port4</name>
            <admin-status>up</admin-status>
        </interface>
    </interfaces-state>
  </data>
</rpc-reply>"""

payload = interface_description



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
    #with manager.connect(host=args.host,
    #                     port=args.port,
    #                     username=args.username,
    #                     password=args.password,
    #                     timeout=90,
    #                     hostkey_verify=False,
    #                     device_params={'name': 'default'}) as m:
#
    #    # execute netconf operation
    #    try:
    #        response = m.get(payload)
    #        #data = ET.fromstring(response)
    #        #print(response)
    #    except RPCError as e:
    #        data = e._raw
#
    #    # beautify output
    #    #print(ET.tostring(data, pretty_print=True))
#
    #    xml_doc = xml.dom.minidom.parseString(response.xml)
    #    description = xml_doc.getElementsByTagName("description")
#
    #    #for item in description:
    #    #  print(item.firstChild.nodeValue)
    #    
    #    #print(description[0].firstChild.nodeValue) 
#
    #    d = xmltodict.parse(response.xml)
    #    #print(d)
    #    root = d['rpc-reply']['data']['interfaces']['interface']
    #    #print(root)
    #    for item in root:
    #      try:
    #        print("{} \n  {}".format(item['name'], item['description']))
    #      except:
    #        pass
    #      #print("{} \n ".format(item['name']))
    #      #print(item)



    data = ET.fromstring(sample_reply)

     # beautify output
    print(ET.tostring(data, pretty_print=True))
     
    xml_doc = xml.dom.minidom.parseString(sample_reply)
    description = xml_doc.getElementsByTagName("name")
    for item in description:
      print(item.firstChild.nodeValue)
