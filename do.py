#!/usr/bin/env python3

import argparse
import datetime
import glob
import os
import shutil
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--venv-freshen', '--vf', action='store_true', help='delete venv and create a new one')
parser.add_argument('--venv-update', '--vu', action='store_true', help=(
    'install human-reqs.txt and write result to requirements.txt, '
    'usually should be preceeded by --venv-freshen, '
    'and activation of venv'
))
parser.add_argument('--venv-install', '--vi', action='store_true', help="install what's specified in requirements.txt")
parser.add_argument('--build', '-b', action='store_true')
parser.add_argument('--run', '-r', action='store_true')
args = parser.parse_args()

DIR = os.path.dirname(os.path.realpath(__file__))

def timestamp():
    return '{:%Y-%m-%d %H:%M:%S.%f}'.format(datetime.datetime.now()).lower()

def invoke(*args, kwargs={}):
    print('-'*20 + ' invoke ' + '-'*20)
    print(timestamp(), os.getcwd(), args, kwargs)
    return subprocess.run(args, check=True, **kwargs)

#===== system =====#
os.chdir(os.path.join(DIR, 'system'))

if args.venv_freshen:
    shutil.rmtree('venv', ignore_errors=True)
    invoke('python', '-m', 'venv', 'venv')

if args.venv_update:
    invoke('pip', 'install', '-r', 'human-reqs.txt')
    with open('requirements.txt', 'w') as frozen:
        frozen.write(invoke('pip', 'freeze', kwargs={'capture_output': True}).stdout.decode())

if args.venv_install:
    invoke('pip', 'install', '-r', 'requirements.txt')

#===== build =====#
if args.build:
    for component_path in glob.glob(os.path.join(DIR, 'components', '*')):
        os.chdir(component_path)
        invoke('cargo', 'build', '--release')

#===== run =====#
if args.run:
    os.chdir(os.path.join(DIR, 'system'))
    invoke('python', '-i', '-c', 'import dlal')
