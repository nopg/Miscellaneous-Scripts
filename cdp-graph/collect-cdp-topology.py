"""
This script builds a CDP tree topology with information from a Cisco device using SSH. The information gathered is
are converted to a JSON file that is used within a HTML page to create a simple network diagram using vis.js.

It uses netmiko, TextFSM and vis.js.
"""
import json
import os
import webbrowser
import sys
import jtextfsm
from netmiko import ConnectHandler
from netmiko.ssh_exception import *

id_counter = 1
found_hosts = []
nodes = []
edges = []

def get_cdp_neighbor_details(ip, username, password):
    """
    get the CDP neighbor detail from the device using SSH

    :param ip: IP address of the device
    :param username: username used for the authentication
    :param password: password used for the authentication
    :param enable_secret: enable secret
    :return:
    """
    # establish a connection to the device

    try:
        ssh_connection = ConnectHandler(
            device_type='cisco_ios',
            ip=ip,
            username=username,
            password=password,
        )
    except NetMikoTimeoutException:
        print("\nSSH session timed trying to connect to the device: {}\n".format(ip))
        return "TIMEOUT"
    except NetMikoAuthenticationException:
        print("\nSSH authentication failed for device: {}\n".format(ip))
        return "AUTHFAIL"
    except ConnectionRefusedError:
        print("\nConnection refused for device: {}\n".format(ip))
        return "CONNECTREFUSED"
    except KeyboardInterrupt:
        print("\nUser interupted connection, closing program.\n")
        sys.exit(0)
    except Exception:
        print("\nUnknown error connecting to device: {}\n".format(ip))
        return "UNKNOWN"

    # prepend the command prompt to the result (used to identify the local device)
    result = ssh_connection.find_prompt() + "\n"

    # execute the show cdp neighbor detail command
    # we increase the delay_factor for this command, because it take some time if many devices are seen by CDP
    result += ssh_connection.send_command("show cdp neighbor detail", delay_factor=2)

    # close SSH connection
    ssh_connection.disconnect()

    return result

def format_fsm_output(re_table, fsm_results):
    """
    FORMAT FSM OUTPUT(LIST OF LIST) INTO PYTHON LIST OF DICTIONARY VALUES BASED ON TEXTFSM TEMPLATE

    :param re_table: re_table from generic fsm search
    :param fsm_results: fsm results from generic fsm search
    :return result: updated list of dictionary values
    """
    result = []
    for item in fsm_results:
        tempdevice = {}
        for position, header in enumerate(re_table.header):
            tempdevice[header] = item[position]
        ## EXCEL DOESN'T LIKE FIELDS STARTING WITH '-' ##
            if  tempdevice[header].startswith('-'):
                tempdevice[header] = '*' + tempdevice[header] + '*'
        result.append(tempdevice)

    return result

def build_topology(target_ip, username, password, recurse_level, from_node=None):

    global found_hosts
    global nodes
    global edges
    global id_counter

    if from_node == None:
        from_node = {"label": "Seed", "id": 0}

    if recurse_level <= 0:
        print(f"recurse level {recurse_level} reached.")
        return

    print(f"\nCollecting CDP information from device {from_node['label']}, "
          f"id {from_node['id']}, recurse {recurse_level} neighbors deep...")

    cdp_det_result = get_cdp_neighbor_details(
        ip=target_ip,
        username=username,
        password=password,
    )

    if cdp_det_result in ("TIMEOUT", "AUTHFAIL", "CONNECTREFUSED", "UNKNOWN"):
        from_node["label"] += f" *** UNREACHABLE ({cdp_det_result}) ***"
        return

    # parse the show cdp details command using TextFSM
    re_table = jtextfsm.TextFSM(open("show_cdp_neighbor_detail.textfsm"))
    fsm_results = re_table.ParseText(cdp_det_result)
    neighbors = format_fsm_output(re_table, fsm_results)

    for nei in neighbors:
        if len(nodes) == 0:
            # add local node (always ID 1)
            node = {
                "id": id_counter,
                "label": nei['LOCAL_HOST'],
                "group": "root_device"
            }

            id_counter += 1
            nodes.append(node)
            found_hosts.append(node["label"])
            from_node = node
            print(f"\tadded ROOT node: {node}")

        # add new node
        remote_node_name = nei['DESTINATION_HOST'].split('.',1)[0] # remove anything after a . (domain name) #
        print(f"Searching for {remote_node_name} in Found hosts")

        if remote_node_name.startswith("SEP"):
            continue
        elif remote_node_name not in found_hosts:
            # add new node
            node = {
                "id": id_counter,
                "label": remote_node_name,
                "title": "<strong>Mgmt-IP:</strong><br>{}<br><br><strong>Platform</strong>:<br> "
                         "{}<br><br><strong>Version:</strong><br> {}".format(nei['MANAGEMENT_IP'], nei['PLATFORM'], nei['SOFTWARE_VERSION']),
                "group": "attached_device"
            }
            nodes.append(node)
            print(f"\tadded node: {node['label']}")

            # add new connection
            edge = {
                "from": from_node["id"],
                "to": id_counter,
                "title": "from: {}<br>to: {}".format(nei['LOCAL_PORT'], nei['REMOTE_PORT']),
                "label": "",
                "value": 0,
                "font": {
                    "align": "top"
                }
            }
            edges.append(edge)
            print(f"\tadded edge from: {edge['from']} to: {edge['to']}")
            found_hosts.append(remote_node_name)

            id_counter += 1

            if 'Cisco IOS' in nei['SOFTWARE_VERSION']:
                next_target = nei['MANAGEMENT_IP']
                build_topology(next_target, username, password, recurse_level - 1, node)
            elif 'AIR' in nei['PLATFORM']:
                print("Neighbor is AP")
            else:
                print("Neighbor not running Cisco IOS")

        else:
            # only add connection of existing device
            print(f"Found {remote_node_name} in Found hosts")

            current_node = None
            for n in nodes:
                if remote_node_name in n["label"]:
                    current_node = n
                    break

            if current_node:
                # create new edge to compare to existing edges
                tempedge = {
                    "from": from_node["id"],
                    "to": current_node["id"],
                    "title": "from: {}<br>to: {}".format(nei['LOCAL_PORT'], nei['REMOTE_PORT']),
                    "label": "",
                    "value": 0,
                    "font": {
                        "align": "top"
                    }
                }
                reversed_tempedge = {
                    "from": current_node["id"],
                    "to": from_node["id"],
                    "title": "from: {}<br>to: {}".format(nei['REMOTE_PORT'], nei['LOCAL_PORT']),
                    "label": "",
                    "value": 0,
                    "font": {
                        "align": "top"
                    }
                }

                # search existing connections
                found_duplicate = False
                duplicate_edge = None

                for edge in edges:

                    if edge == tempedge or edge == reversed_tempedge:
                        found_duplicate = True
                        break
                    # unique connection / possible loop?
                    else:
                        found_duplicate = False
                        redundant_edge = edge

                if found_duplicate:
                    print("\tFound duplicate edge! Next node.")
                    continue

                # extra connection, increase the value of the link
                elif redundant_edge["to"] == tempedge["to"] and redundant_edge["from"] == tempedge["from"]:
                    redundant_edge["value"] += 10
                    redundant_edge["title"] += "<hr>from: {}<br>to: {}".format(nei['LOCAL_PORT'], nei['REMOTE_PORT'])
                    print(f"\tadded redundant edge from: {nei['LOCAL_PORT']} to: {nei['REMOTE_PORT']}")
                    continue
                else:
                    edges.append(tempedge)
                    print(f"\tadded possible LOOP? edge from: {tempedge['from']} to: {tempedge['to']}")

            else:
                # not found
                print("\thost {} should exist, but was not found in the dictionary.".format(remote_node_name))

    data = {
        "nodes": nodes,
        "edges": edges
    }

    return data


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("\nplease provide the following arguments:")
        print("\tcollect-cdp-information.py <ip> <username> <password> <recurse_level>\n\n")
        sys.exit(0)

    target_ip = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    recurse = sys.argv[4]

    topo = build_topology(target_ip, username, password, int(recurse))
    print("\n\nwrite results to data.js...\n")
    datajs = "var data = " + json.dumps(topo, indent=4)
    if os.path.exists("data.js"):
        os.remove("data.js")

    f = open("data.js", "w")
    f.write(datajs)
    f.close()

    webbrowser.open_new_tab(os.path.abspath("data.js"))

    print("Finished, open result.html with browser for output.")
