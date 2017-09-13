var data = {
    "nodes": [
        {
            "id": 1,
            "label": "R1",
            "group": "root_device"
        },
        {
            "id": 2,
            "label": "EN-Lab-Switch.compunet.local",
            "title": "<strong>Mgmt-IP:</strong><br>172.20.254.5<br><br><strong>Platform</strong>:<br> cisco WS-C3750-48TS<br><br><strong>Version:</strong><br> Cisco IOS Software, C3750 Software (C3750-IPBASEK9-M), Version 12.2(55)SE4, RELEASE SOFTWARE (fc1)",
            "group": "attached_device"
        },
        {
            "id": 3,
            "label": "R2.cisco.com",
            "title": "<strong>Mgmt-IP:</strong><br>172.20.100.59<br><br><strong>Platform</strong>:<br> Cisco 3745<br><br><strong>Version:</strong><br> Cisco IOS Software, 3700 Software (C3745-ADVENTERPRISEK9-M), Version 12.4(15)T14, RELEASE SOFTWARE (fc2)",
            "group": "attached_device"
        },
        {
            "id": 4,
            "label": "R3.cisco.com",
            "title": "<strong>Mgmt-IP:</strong><br>172.20.100.58<br><br><strong>Platform</strong>:<br> Cisco <br><br><strong>Version:</strong><br> Cisco IOS Software, IOSv Software (VIOS-ADVENTERPRISEK9-M), Version 15.6(2)T, RELEASE SOFTWARE (fc2)",
            "group": "attached_device"
        }
    ],
    "edges": [
        {
            "from": 1,
            "to": 2,
            "title": "from: FastEthernet0/0<br>to: FastEthernet1/0/36",
            "label": "",
            "value": 0,
            "font": {
                "align": "top"
            }
        },
        {
            "from": 1,
            "to": 3,
            "title": "from: FastEthernet0/0<br>to: FastEthernet0/0",
            "label": "",
            "value": 0,
            "font": {
                "align": "top"
            }
        },
        {
            "from": 1,
            "to": 4,
            "title": "from: FastEthernet0/0<br>to: GigabitEthernet0/0",
            "label": "",
            "value": 0,
            "font": {
                "align": "top"
            }
        }
    ]
}