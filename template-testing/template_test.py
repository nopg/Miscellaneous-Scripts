from jinja2 import Template

# Create jinja template
with open("template.j2", "r") as fin:
    template1 = Template(fin.read())

# Variables
vars = {
    "hostname": "core1",
    "loopback_ip_mask": "99.99.99.99/32",
    "vlan2_ip_mask": "2.2.2.1/24",
    "vlan3_ip_mask": "3.3.3.1/24",
    "router_id": "99.99.99.99",
}

# Render template (create real config)
output1 = template1.render(**vars)

# Print Output
print(output1)
