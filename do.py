#!/usr/bin/env python3

import argparse
import datetime
import glob
import os
import re
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
parser.add_argument('--component-new')
parser.add_argument('--build', '-b', action='store_true')
parser.add_argument('--run', '-r', nargs='?', const=True)
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

#===== components =====#
if args.component_new:
    os.chdir(os.path.join(DIR, 'components'))
    invoke('cargo', 'new', '--lib', args.component_new)
    with open(os.path.join(args.component_new, 'Cargo.toml')) as file:
        contents = file.read()
    contents = re.sub('version.*'       , 'version = 1.0.0'                                 , contents)
    contents = re.sub('#.*'             , ''                                                , contents)
    contents = re.sub('\[dependencies\]', '[lib]\ncrate-type = ["cdylib"]\n\n[dependencies]', contents)
    while '\n\n\n' in contents:
        contents = re.sub('\n\n\n', '\n\n', contents)
    with open(os.path.join(args.component_new, 'Cargo.toml'), 'w') as file:
        file.write(contents)

#===== build =====#
if args.build:
    for component_path in glob.glob(os.path.join(DIR, 'components', '*')):
        if os.path.basename(component_path) == 'base': continue
        os.chdir(component_path)
        invoke('cargo', 'build', '--release')

#===== run =====#
if args.run == True:
    os.chdir(os.path.join(DIR, 'system'))
    invoke('python', '-i', '-c', 'import dlal')
elif args.run:
    if 'PYTHONPATH' in os.environ:
        os.environ['PYTHONPATH'] += os.pathsep + os.path.join(DIR, 'system')
    else:
        os.environ['PYTHONPATH'] = os.path.join(DIR, 'system')
    os.chdir(os.path.join(DIR))
    invoke('python', '-i', args.run)
