import sys
import argparse
import csv
from getpass import getpass
import logging
import asyncio

import yaml
from scrapli import AsyncScrapli
from scrapli.helper import textfsm_parse
from scrapli.response import Response
import markdown

DEBUG = False
DEBMAXLINES = 1

#logging.basicConfig(filename="scrapli.log", level=logging.WARNING) ## Not currently working??


def load_yaml(filename):
    try:
        with open(filename) as _:
            return yaml.load(_, Loader=yaml.SafeLoader)
    except:
        print("Invalid device file!")
        sys.exit(0)


## Stolen from: https://github.com/codazoda/tomark/blob/master/tomark/tomark.py (MIT Licensed)
def to_markdown_table(listOfDicts):
    """Loop through a list of dicts and return a markdown table as a multi-line string.
    listOfDicts -- A list of dictionaries, each dict is a row
    """
    markdowntable = ""
    # Make a string of all the keys in the first dict with pipes before after and between each key
    markdownheader = '| ' + ' | '.join(map(str, listOfDicts[0].keys())) + ' |'
    # Make a header separator line with dashes instead of key names
    markdownheaderseparator = '|:-----' * len(listOfDicts[0].keys()) + '|'
    # Add the header row and separator to the table
    markdowntable += markdownheader + '\n'
    markdowntable += markdownheaderseparator + '\n'
    # Loop through the list of dictionaries outputting the rows
    for row in listOfDicts:
        markdownrow = ""
        for key, col in row.items():
            temp = str(col) ## Added by me, not in original
            if '\n' in col:
                temp = col.replace('\n',' |\n| | ')
            markdownrow += '| ' + temp + ' '
        markdowntable += markdownrow + '|' + '\n'
    return markdowntable


def build_csv(output, filename):
    """
    BUILD CSV BASED ON AN EXISTING DICTIONARY

    :param output: existing dictionary to be written
    :param filename: filename to create csv
    :return:
    """
    
    if output:
        pass
    else:
        return None
        
    print("Building CSV...")
    headers = list(output[0].keys())
    fout = open(filename, 'w')
    writer = csv.DictWriter(fout, fieldnames=headers, lineterminator='\n')
    writer.writeheader()
    writer.writerows(output)
    fout.close()


def build_device_list(filename):
    devices = load_yaml(filename)
    print(devices)

    IOSXE_DEVICES = []
    
    # Build list of devices
    for host in devices["IOS"]:
        IOSXE_DEVICES.append( {
            "host": host,
            "transport": "asyncssh",
            "auth_username": username,
            "auth_password": password,
            "auth_strict_key": False,
            "platform": "cisco_iosxe",
            "transport_options": {
                "asyncssh": {
                    "encryption_algs": ["aes128-cbc", "aes192-cbc", "aes256-ctr", "aes192-ctr"]
                }
            }
        } )
    
    return IOSXE_DEVICES


def format_sh_ver_results(sh_ver_results):
    dict_results = []
    failed = []
    dont_want_these_headers = ["uptime_years", "uptime_weeks", "uptime_days", "uptime_hours", "uptime_minutes", "serial", "mac"]

    for result in sh_ver_results:

        if result.failed == True:
            failed.append(result)
        else:
            textfsm = result.textfsm_parse_output()[0] ## find better way to handle [0]
            for key in dont_want_these_headers:
                textfsm.pop(key, None)
            dict_results.append(textfsm)
    
    return dict_results, failed


def format_manual_results(manual_results):
    dict_results = []

    for result in manual_results:
        temp = {}
        temp["host"] = result.host
        temp["result"] = str(result.result)
        dict_results.append(temp)

    # print(dict_results)
    # sys.exit(0)
    return dict_results


def create_outputs(results, filename):
    # Create markdown
    md_results = to_markdown_table(results)

    # Create html
    html = "<style>table{border:3px solid black;}th, td{border:1px solid black;}</style>"
    html += markdown.markdown(md_results, extensions=['tables'])

    # Write Outputs
    print("Building markdown")
    with open(f"{filename}.md", 'w') as fin:
        fin.write(md_results)
    
    print("Building html")
    with open(f"{filename}.html", 'w') as fin:
        fin.write(html)

    build_csv(results, f"{filename}.csv")


async def get_show_command(device: dict, command: str) -> dict: # Actually List(Dict)---to update
    try:
        async with AsyncScrapli(**device) as conn:
            version_response = await conn.send_command(command)
        
        return version_response

    except Exception as e:
        response = Response(device["host"],command)
        response.result = e

        return response



async def async_show_command(username: str, password: str, devices: dict, command: str):
 
    # Async run em all
    coroutines = [get_show_command(device, command) for device in devices]
    sh_command_results = await asyncio.gather(*coroutines)
    
    return sh_command_results


def manual_command(username,password,filename,command):
    IOSXE_DEVICES = build_device_list(filename)

    manual_command_results = asyncio.get_event_loop().run_until_complete(async_show_command(username, password, IOSXE_DEVICES, command))

    for result in manual_command_results:
        print(result.host)
        print(result.result)


    # Create useable output dictionary / table for ALL devices
    dict_results = format_manual_results(manual_command_results)

    create_outputs(dict_results, "manual")



def create_inventory(username: str, password: str, filename: str) -> None:
    
    IOSXE_DEVICES = build_device_list(filename)

    sh_ver_results = asyncio.get_event_loop().run_until_complete(async_show_command(username, password, IOSXE_DEVICES, "show version"))

    print("Output: ")

    # Create useable output dictionary / table for ALL devices
    dict_results, failed = format_sh_ver_results(sh_ver_results)

    # Create markdown
    md_results = to_markdown_table(dict_results)

    # Create html
    html = "<style>table{border:3px solid black;}th, td{border:1px solid black;}</style>"
    html += markdown.markdown(md_results, extensions=['tables'])

    # Add failure text if necessary
    if failed:
        failure_text = """\n\n
        We failed to get output from the following devices:\n
        Host\t\t\tError:\n
        -----------------------------------------\n
        """
        for failure in failed:
            failure_text += f"{failure.host}\t{failure.result}\n"
        failure_text += "\n"

        md_results += failure_text
        html += markdown.markdown(failure_text)

        print(failure_text)

    # Write Outputs
    print("Building markdown")
    with open(f"test.md", 'w') as fin:
        fin.write(md_results)
    
    print("Building html")
    with open(f"test.html", 'w') as fin:
        fin.write(html)

    build_csv(dict_results, "test.csv")


# def load_manual(username: str, password: str, filename: str) -> None:
#     asyncio.get_event_loop().run_until_complete(main(username, password, filename))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Please use this syntax:")
    parser.add_argument("-u", "--username", help="Username for Cisco Devices", type=str)
    parser.add_argument("-p", "--password", help="Password for Cisco Devices", type=str)
    parser.add_argument("-f", "--filename", help="Device List File (YAML)", type=str)
    parser.add_argument("-d", "--directory", help="Directory containing 'show version' output.", type=str)
    parser.add_argument("-i", "--inventory", help="Create a new inventory only.(any value)", type=str)
    parser.add_argument("-c", "--command", help="Send this command", type=str)
    args = parser.parse_args()

    # if args.directory:
    #     load_manual()
    #     sys.exit(0)

    username = args.username
    password = args.password
    filename = args.filename
    command = args.command

    if not username:
        username = input("Username for Cisco Devices: ")
    if not password:
        password = getpass("Password for Cisco Devices: ")
    if not filename:
        filename = input("Device List File: ")

    if args.inventory:
        create_inventory(username,password,filename)
    
    if command:
        manual_command(username, password, filename, command)

    print("Done.")