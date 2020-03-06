var data = {
    "nodes": [
        {
            "id": 1,
            "label": "8350-MDF-05",
            "group": "root_device"
        },
        {
            "id": 2,
            "label": "8350-MDF-01",
            "title": "<strong>Mgmt-IP:</strong><br>10.15.1.1<br><br><strong>Platform</strong>:<br> cisco C9300-24T<br><br><strong>Version:</strong><br> Cisco IOS Software [Everest], Catalyst L3 Switch Software (CAT9K_IOSXE), Version 16.6.5, RELEASE SOFTWARE (fc3)",
            "group": "attached_device"
        },
        {
            "id": 3,
            "label": "8360-AXT-11",
            "title": "<strong>Mgmt-IP:</strong><br>10.15.1.11<br><br><strong>Platform</strong>:<br> cisco C9200L-24P-4X<br><br><strong>Version:</strong><br> Cisco IOS Software [Fuji], Catalyst L3 Switch Software (CAT9K_LITE_IOSXE), Version 16.9.3, RELEASE SOFTWARE (fc2)",
            "group": "attached_device"
        },
        {
            "id": 4,
            "label": "8350-MDF-04",
            "title": "<strong>Mgmt-IP:</strong><br>10.15.1.4<br><br><strong>Platform</strong>:<br> cisco WS-C2960X-48FPD-L<br><br><strong>Version:</strong><br> Cisco IOS Software, C2960X Software (C2960X-UNIVERSALK9-M), Version 15.2(2)E7, RELEASE SOFTWARE (fc3)",
            "group": "attached_device"
        },
        {
            "id": 5,
            "label": "8350-MDF-07",
            "title": "<strong>Mgmt-IP:</strong><br>10.15.1.7<br><br><strong>Platform</strong>:<br> cisco C9200L-48P-4X<br><br><strong>Version:</strong><br> Cisco IOS Software [Fuji], Catalyst L3 Switch Software (CAT9K_LITE_IOSXE), Version 16.9.2, RELEASE SOFTWARE (fc4)",
            "group": "attached_device"
        },
        {
            "id": 6,
            "label": "8370-BRICK-31",
            "title": "<strong>Mgmt-IP:</strong><br>10.15.1.31<br><br><strong>Platform</strong>:<br> cisco C9200L-48P-4X<br><br><strong>Version:</strong><br> Cisco IOS Software [Fuji], Catalyst L3 Switch Software (CAT9K_LITE_IOSXE), Version 16.9.2, RELEASE SOFTWARE (fc4)",
            "group": "attached_device"
        },
        {
            "id": 7,
            "label": "Switch-9500-a1",
            "title": "<strong>Mgmt-IP:</strong><br>10.0.100.81<br><br><strong>Platform</strong>:<br> cisco C9500-48Y4C<br><br><strong>Version:</strong><br> Cisco IOS Software [Gibraltar], Catalyst L3 Switch Software (CAT9K_IOSXE), Version 16.10.1, RELEASE SOFTWARE (fc3)",
            "group": "attached_device"
        },
        {
            "id": 8,
            "label": "8350-XFS-08",
            "title": "<strong>Mgmt-IP:</strong><br>10.15.1.8<br><br><strong>Platform</strong>:<br> cisco WS-C3560C-8PC-S<br><br><strong>Version:</strong><br> Cisco IOS Software, C3560C Software (C3560c405-UNIVERSALK9-M), Version 15.2(2)E7, RELEASE SOFTWARE (fc3)",
            "group": "attached_device"
        }
    ],
    "edges": [
        {
            "from": 1,
            "to": 2,
            "title": "from: TenGigabitEthernet3/0/1<br>to: TenGigabitEthernet2/1/5",
            "label": "",
            "value": 0,
            "font": {
                "align": "top"
            }
        },
        {
            "from": 2,
            "to": 3,
            "title": "from: TenGigabitEthernet2/1/3<br>to: TenGigabitEthernet2/1/1<hr>from: TenGigabitEthernet1/1/3<br>to: TenGigabitEthernet1/1/1",
            "label": "",
            "value": 10,
            "font": {
                "align": "top"
            }
        },
        {
            "from": 2,
            "to": 1,
            "title": "from: TenGigabitEthernet1/1/5<br>to: TenGigabitEthernet1/0/1",
            "label": "",
            "value": 0,
            "font": {
                "align": "top"
            }
        },
        {
            "from": 2,
            "to": 4,
            "title": "from: TenGigabitEthernet2/1/4<br>to: TenGigabitEthernet3/0/1<hr>from: TenGigabitEthernet1/1/4<br>to: TenGigabitEthernet1/0/1",
            "label": "",
            "value": 10,
            "font": {
                "align": "top"
            }
        },
        {
            "from": 2,
            "to": 5,
            "title": "from: TenGigabitEthernet2/1/6<br>to: TenGigabitEthernet2/1/1<hr>from: TenGigabitEthernet1/1/6<br>to: TenGigabitEthernet1/1/1",
            "label": "",
            "value": 10,
            "font": {
                "align": "top"
            }
        },
        {
            "from": 2,
            "to": 6,
            "title": "from: TenGigabitEthernet1/1/2<br>to: TenGigabitEthernet1/1/1",
            "label": "",
            "value": 0,
            "font": {
                "align": "top"
            }
        },
        {
            "from": 2,
            "to": 7,
            "title": "from: TenGigabitEthernet2/1/1<br>to: TwentyFiveGigE2/0/2<hr>from: TenGigabitEthernet1/1/1<br>to: TwentyFiveGigE1/0/2",
            "label": "",
            "value": 10,
            "font": {
                "align": "top"
            }
        },
        {
            "from": 1,
            "to": 8,
            "title": "from: GigabitEthernet1/0/33<br>to: GigabitEthernet0/1",
            "label": "",
            "value": 0,
            "font": {
                "align": "top"
            }
        }
    ]
}