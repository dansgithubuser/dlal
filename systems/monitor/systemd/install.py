#!/usr/bin/env python3

import os
import string
import subprocess
import sys

DIR = os.path.dirname(os.path.realpath(__file__))

def invoke(invocation):
    subprocess.run(invocation.split(), check=True)

if os.geteuid() != 0:
    raise Exception('Must be root user.')

print('short unique description:')
desc = input()
print()
script_path = os.path.abspath(os.path.join(DIR, '..'))
exec_start = f'{sys.executable} -u {script_path}'
with open(os.path.join(DIR, 'template.service')) as f:
    template = f.read()
service_text = template.format(
    description=desc,
    python_path=os.path.abspath(os.path.join(DIR, '..', '..', '..', 'skeleton')),
    exec_start=exec_start,
)
remove_punctuation = str.maketrans('', '', string.punctuation)
service_file_name = 'dlal_' + desc.translate(remove_punctuation).replace(' ', '_').lower() + '.service'
service_path = f'/etc/systemd/system/{service_file_name}'
print(f"I will write the following to '{service_path}':")
print()
print(service_text)
print()
print('OK? Enter to proceed, ctrl-c to abort.')
input()
with open('.service.tmp', 'w') as f:
    f.write(service_text)
os.rename('.service.tmp', service_path)
invoke('systemctl daemon-reload')
invoke(f'systemctl enable {service_file_name}')
print('Service is installed & enabled. Start it now? Enter y if so, or anything else otherwise.')
if input() == 'y':
    invoke(f'systemctl restart {service_file_name}')
