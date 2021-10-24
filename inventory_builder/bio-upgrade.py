import argparse
from getpass import getpass

import inventory_builder


def main():
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Please use this syntax:")
    parser.add_argument("-u", "--username", help="Username for Cisco Devices", type=str)
    parser.add_argument("-p", "--password", help="Password for Cisco Devices", type=str)
    parser.add_argument("-f", "--filename", help="Device List File (YAML)", type=str)
    parser.add_argument("-d", "--directory", help="Directory containing 'show version' output.", type=str)
    parser.add_argument("-i", "--inventory", help="Create a new inventory only.(any value)", type=str)

    args = parser.parse_args()
    
    username = args.username
    password = args.password
    filename = args.filename

    if not username:
        username = input("Username for Cisco Devices: ")
    if not password:
        password = getpass("Password for Cisco Devices: ")
    if not filename:
        filename = input("Device List File: ")

    if args.inventory:
        inventory_builder.create_inventory_manual(username, password, filename)

    main()
    
    print("hi")