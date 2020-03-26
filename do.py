#!/usr/bin/env python3

import argparse
import datetime
import glob
import os
import re
import shutil
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--venv-freshen', '--vf', action='store_true',
    help='delete venv and create a new one'
)
parser.add_argument('--venv-update', '--vu', action='store_true', help=(
    'install human-reqs.txt and write result to requirements.txt, '
    'usually should be preceeded by --venv-freshen, '
    'and activation of venv'
))
parser.add_argument('--venv-install', '--vi', action='store_true',
    help="install what's specified in requirements.txt"
)
parser.add_argument('--component-new')
parser.add_argument('--build', '-b', action='store_true')
parser.add_argument('--run', '-r', nargs='?', const=True)
parser.add_argument('--style-check', '--style', action='store_true')
parser.add_argument('--style-rust-fix', action='store_true')
args = parser.parse_args()

DIR = os.path.dirname(os.path.realpath(__file__))

def timestamp():
    return '{:%Y-%m-%d %H:%M:%S.%f}'.format(datetime.datetime.now()).lower()

def invoke(*args, kwargs={}):
    if 'check' not in kwargs: kwargs['check'] = True
    print('-' * 20 + ' invoke ' + '-' * 20)
    print(timestamp(), os.getcwd(), args, kwargs)
    return subprocess.run(args, **kwargs)

# ===== skeleton ===== #
os.chdir(os.path.join(DIR, 'skeleton'))

if args.venv_freshen:
    shutil.rmtree('venv', ignore_errors=True)
    invoke('python', '-m', 'venv', 'venv')

if args.venv_update:
    invoke('pip', 'install', '-r', 'human-reqs.txt')
    with open('requirements.txt', 'w') as frozen:
        frozen.write(invoke(
            'pip', 'freeze', kwargs={'capture_output': True}
        ).stdout.decode())

if args.venv_install:
    invoke('pip', 'install', '-r', 'requirements.txt')

# ===== components ===== #
if args.component_new:
    os.chdir(os.path.join(DIR, 'components'))
    invoke('cargo', 'new', '--lib', args.component_new)
    def mod_file(path, subs=[], reps=[]):
        with open(path) as file: contents = file.read()
        for patt, repl in subs: contents = re.sub(patt, repl, contents)
        for patt, repl in reps:
            while patt in contents:
                contents = re.sub(patt, repl, contents)
        with open(path, 'w') as file: file.write(contents)
    mod_file(os.path.join(args.component_new, 'Cargo.toml'),
        [
            ('version.*', 'version = "1.0.0"'),
            ('#.*', ''),
            (
                r'\[dependencies\]',
                (
                    r'[lib]\n'
                    r'crate-type = ["cdylib"]\n'
                    r'\n'
                    r'[dependencies]\n'
                    r'dlal-component-base = { path = "../base" }'
                ),
            ),
        ],
        [('\n\n\n', '\n\n')],
    )
    mod_file(os.path.join(args.component_new, 'src', 'lib.rs'),
        [(
            r'(.|\n)+',
            (
                r'use dlal_component_base::{gen_component};\n'
                r'\n'
                r'pub struct Specifics {\n'
                r'}\n'
                r'\n'
                r'gen_component!(Specifics);\n'
                r'\n'
                r'impl SpecificsTrait for Specifics {\n'
                r'    fn new() -> Self {\n'
                r'        Self {\n'
                r'        }\n'
                r'    }\n'
                r'\n'
                r'    //optional\n'
                r'    fn register_commands(&self, commands: &mut CommandMap) {}\n'
                r'    fn evaluate(&mut self) {}\n'
                r'    fn midi(&mut self, _msg: &[u8]) {}\n'
                r'    fn audio(&mut self) -> Option<&mut[f32]> { None }\n'
                r'}\n'
            ),
        )],
    )

# ===== build ===== #
if args.build:
    for component_path in glob.glob(os.path.join(DIR, 'components', '*')):
        if os.path.basename(component_path) == 'base': continue
        os.chdir(component_path)
        invoke('cargo', 'build', '--release')

# ===== run ===== #
if args.run is True:
    os.chdir(os.path.join(DIR, 'skeleton'))
    invoke('python', '-i', '-c', 'import dlal')
elif args.run:
    if 'PYTHONPATH' in os.environ:
        os.environ['PYTHONPATH'] += os.pathsep + os.path.join(DIR, 'skeleton')
    else:
        os.environ['PYTHONPATH'] = os.path.join(DIR, 'skeleton')
    os.chdir(os.path.join(DIR))
    invoke('python', '-i', args.run)

# ===== style ===== #
if args.style_check or args.style_rust_fix:
    result = 0
    for i in glob.glob(os.path.join(DIR, 'components', '*')):
        os.chdir(i)
        invoke_args = ['cargo', 'fmt', '--',
            '--config-path', os.path.join(DIR, '.rustfml.toml'),
        ]
        if args.style_check: invoke_args.append('--check')
        result |= invoke(*invoke_args, kwargs={'check': False}).returncode
    if not args.style_check: sys.exit(0)
    def check_py(path):
        global result
        result |= invoke(
            'pycodestyle',
            '--ignore',
            'E124,E128,E203,E301,E302,E305,E701,E704,E711',
            path,
            kwargs={'check': False},
        ).returncode
    for i in glob.glob(os.path.join(DIR, 'skeleton', 'dlal', '*.py')):
        check_py(i)
    check_py(os.path.join(DIR, 'do.py'))
    for i in glob.glob(os.path.join(DIR, 'systems', '*.py')):
        check_py(i)
    if result: sys.exit(1)
