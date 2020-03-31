#!/usr/bin/env python3

import argparse
import datetime
import glob
import http.server
import os
import re
import shutil
import socketserver
import subprocess
import sys
import webbrowser

parser = argparse.ArgumentParser()
parser.add_argument('--venv-freshen', '--vf', action='store_true', help=(
    'delete venv and create a new one, '
    '`. venv-off` to deactivate venv if necessary'
))
parser.add_argument('--venv-update', '--vu', action='store_true', help=(
    'install human-reqs.txt and write result to requirements.txt, '
    'usually should be preceeded by `./do.py --vf; . venv-on`, '
))
parser.add_argument('--venv-install', '--vi', action='store_true',
    help="install what's specified in requirements.txt"
)
parser.add_argument('--component-new')
parser.add_argument('--build', '-b', nargs='*')
parser.add_argument('--run', '-r', nargs='*', help=(
    'run interactive Python with dlal imported, '
    'or run specified system, optionally with args'
))
parser.add_argument('--web', '-w', action='store_true',
    help='open web interface and run web server'
)
parser.add_argument('--style-check', '--style', action='store_true')
parser.add_argument('--style-rust-fix', action='store_true')
args = parser.parse_args()

DIR = os.path.dirname(os.path.realpath(__file__))

def timestamp():
    return '{:%Y-%m-%d %H:%M:%S.%f}'.format(datetime.datetime.now()).lower()

def invoke(*args, kwargs={}, title='invoke', fmt='{ts} {cwd} {args} {kwargs}'):
    if 'check' not in kwargs: kwargs['check'] = True
    if title:
        title = ' ' + title + ' '
    else:
        title = ''
    print('-' * 20 + title + '-' * 20)
    ts = timestamp()
    cwd = os.getcwd()
    if fmt: exec(f'print(f"{fmt}")')
    result = subprocess.run(args, **kwargs)
    print()
    return result

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
new_lib_rs = '''\
use dlal_component_base::{gen_component};

pub struct Specifics {
}

gen_component!(Specifics);

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
        }
    }

    //optional
    fn register_commands(&self, commands: &mut CommandMap) {}
    fn evaluate(&mut self) {}
    fn midi(&mut self, _msg: &[u8]) {}
    fn audio(&mut self) -> Option<&mut [f32]> { None }
}'''

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
    mod_file(
        os.path.join(args.component_new, 'Cargo.toml'),
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
        [(r'(.|\n)+', new_lib_rs)],
    )

# ===== build ===== #
if args.build is not None:
    for component_path in glob.glob(os.path.join(DIR, 'components', '*')):
        component = os.path.basename(component_path)
        if args.build and component not in args.build: continue
        if component == 'base': continue
        os.chdir(component_path)
        invoke(
            'cargo', 'build', '--release',
            title=component,
            fmt=None,
        )

# ===== run ===== #
if args.run or args.run == []:
    os.chdir(os.path.join(DIR))
    if 'PYTHONPATH' in os.environ:
        os.environ['PYTHONPATH'] += os.pathsep + os.path.join(DIR, 'skeleton')
    else:
        os.environ['PYTHONPATH'] = os.path.join(DIR, 'skeleton')
    if args.run:
        invoke('python', '-i', *args.run)
    else:
        invoke('python', '-i', '-c', 'import dlal')

# ===== web ===== #
if args.web:
    os.chdir(DIR)
    webbrowser.open_new_tab('http://localhost:8000/web/index.html')
    with socketserver.TCPServer(
        ('', 8000),
        http.server.SimpleHTTPRequestHandler
    ) as httpd:
        httpd.serve_forever()

# ===== style ===== #
if args.style_check or args.style_rust_fix:
    result = 0
    def run_on_components(f):
        global result
        for i in glob.glob(os.path.join(DIR, 'components', '*')):
            os.chdir(i)
            result |= f(i)
        return result
    # rust - fmt
    def rust_fmt(path):
        invoke_args = ['cargo', 'fmt', '--',
            '--config-path', os.path.join(DIR, '.rustfml.toml'),
        ]
        if args.style_check: invoke_args.append('--check')
        return invoke(
            *invoke_args,
            kwargs={'check': False},
            title='fmt',
            fmt=os.path.relpath(path, DIR)
        ).returncode
    run_on_components(rust_fmt)
    if not args.style_check: sys.exit(result)
    # rust - clippy
    def rust_clippy(path):
        return invoke(
            'cargo', 'clippy', '--',
                '-A', 'clippy::not_unsafe_ptr_arg_deref',
                '-A', 'clippy::single_match',
                '-A', 'clippy::unnecessary_cast',
                '-A', 'clippy::transmute_ptr_to_ptr',
                '-A', 'clippy::needless_range_loop',
                '-A', 'clippy::vec_box',
            kwargs={'check': False},
            title='clippy',
            fmt=os.path.relpath(path, DIR)
        ).returncode
    run_on_components(rust_clippy)
    # python
    os.chdir(DIR)
    def check_py(path):
        global result
        result |= invoke(
            'pycodestyle',
            '--ignore',
            ','.join([
                'E124', 'E128', 'E131',
                'E203', 'E226',
                'E301', 'E302', 'E305', 'E306',
                'E402',
                'E701', 'E704', 'E711', 'E722',
            ]),
            path,
            kwargs={'check': False},
            title='pycodestyle',
            fmt=os.path.relpath(path, DIR),
        ).returncode
    for i in glob.glob(os.path.join(DIR, 'skeleton', 'dlal', '*.py')):
        check_py(i)
    check_py(os.path.join(DIR, 'do.py'))
    for i in glob.glob(os.path.join(DIR, 'systems', '*.py')):
        check_py(i)
    if result: sys.exit(1)
