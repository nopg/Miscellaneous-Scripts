from jinja2 import Template

# Create Bootstrap File
with open("template.j2", "r") as fin:
    template1 = Template(fin.read())

vars = {
    "hostname": "core1",
    "loopback_ip_mask": "99.99.99.99/32",
    "vlan2_ip_mask": "2.2.2.1/24",
    "vlan3_ip_mask": "3.3.3.1/24",
    "router_id": "99.99.99.99",
}

output1 = template1.render(**vars)

print(output1)
