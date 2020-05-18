#!/usr/bin/env python3

import argparse
import collections
import datetime
import glob
import http.server
import os
import pprint
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
parser.add_argument('--component-new', '--cn', nargs='+')
parser.add_argument('--component-info', '--ci')
parser.add_argument('--component-base-docs', '--cbd', action='store_true')
parser.add_argument('--component-matrix', '--cm', action='store_true')
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
use dlal_component_base::{
    command,
    gen_component,
    join,
    json,
    marg,
    multi,
    uni,
    View,
};

use std::vec::Vec;

#[derive(Default)]
pub struct Specifics {
    samples_per_evaluation: usize,
    sample_rate: u32,
    outputs: Vec<View>,
    output: Option<View>,
}

gen_component!(Specifics, {"in": ["?"], "out": ["?"]});

impl SpecificsTrait for Specifics {
    fn new() -> Self {
        Self {
            ..Default::default()
        }
    }

    fn register_commands(&self, commands: &mut CommandMap) {
        join!(
            commands,
            |soul, body| {
                join!(samples_per_evaluation soul, body);
                join!(sample_rate soul, body);
                Ok(None)
            },
            ["samples_per_evaluation", "sample_rate"],
        );
        multi!(connect commands, false);
        uni!(connect commands, false);
        command!(
            commands,
            "value",
            |soul, body| {
                if let Ok(v) = marg!(arg_num &body, 0) {
                    soul.value = v;
                }
                Ok(Some(json!(soul.value)))
            },
            {
                "args": [{
                    "name": "value",
                    "optional": true,
                }],
            },
        );
        command!(
            commands,
            "to_json",
            |soul, _body| {
                Ok(Some(json!({
                    "value": soul.value,
                })))
            },
            {},
        );
        command!(
            commands,
            "from_json",
            |soul, body| {
                let j = marg!(arg &body, 0)?;
                soul.value = marg!(json_num marg!(json_get j, "value")?)?;
                Ok(None)
            },
            { "args": ["json"] },
        );
    }

    fn midi(&mut self, msg: &[u8]) {
    }

    fn audio(&mut self) -> Option<&mut [f32]> {
        None
    }

    fn evaluate(&mut self) {
    }
}'''

if args.component_new:
    os.chdir(os.path.join(DIR, 'components'))
    name = args.component_new[0]
    invoke('cargo', 'new', '--lib', name)
    def mod_file(path, subs=[], reps=[]):
        with open(path) as file: contents = file.read()
        for patt, repl in subs: contents = re.sub(patt, repl, contents)
        for patt, repl in reps:
            while patt in contents:
                contents = re.sub(patt, repl, contents)
        with open(path, 'w') as file: file.write(contents)
    mod_file(
        os.path.join(name, 'Cargo.toml'),
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
    mod_file(os.path.join(name, 'src', 'lib.rs'),
        [(r'(.|\n)+', new_lib_rs)],
    )
    if len(args.component_new) > 1:
        with open(os.path.join(name, 'README.md'), 'w') as file:
            file.write(' '.join(args.component_new[1:])+'\n')

if args.component_info:
    os.chdir(DIR)
    readme_path = os.path.join('components', args.component_info, 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path) as readme:
            print(readme.read())
    sys.path.append(os.path.join(DIR, 'skeleton'))
    import dlal
    component = dlal.component_class(args.component_info)()
    print('----- info -----')
    pprint.pprint(component.info())
    print()
    print('----- commands -----')
    for command in component.list():
        print(command['name'])
        pprint.pprint(command)
        print()

if args.component_base_docs:
    base_dir = os.path.join(DIR, 'components', 'base')
    os.chdir(base_dir)
    invoke('cargo', 'doc')
    webbrowser.open_new_tab(os.path.join(
        base_dir, 'target', 'doc', 'dlal_component_base', 'index.html'
    ))

if args.component_matrix:
    os.chdir(DIR)
    sys.path.append(os.path.join(DIR, 'skeleton'))
    import dlal
    kinds = dlal.component_kinds()
    def get_cat(interface):
        if not interface: return 'none'
        interface = [i.replace('*', '') for i in interface]
        interface = sorted(
            interface,
            key=lambda i: {'audio': 0, 'midi': 1, 'cmd': 2}[i],
        )
        if interface == 'audio+midi+cmd': return 'all'
        return '+'.join(interface)
    def get_short(interface):
        return '+'.join([
            i
                .replace('audio', 'aud')
                .replace('midi', 'mid')
            for i in interface
        ])
    matrix = collections.defaultdict(lambda: collections.defaultdict(list))
    for kind in kinds:
        info = dlal.component_class(kind)().info()
        matrix[get_cat(info['in'])][get_cat(info['out'])].append((kind, info))
    cats = [
        'audio',
        'audio+midi',
        'midi',
        'midi+cmd',
        'cmd',
        'audio+cmd',
        'none',
        'all',
        '?',
    ]
    with open('matrix.html', 'w') as file:
        def w(x): file.write(x)
        w('''<style>
            * {
                font-family: monospace;
            }

            .from-to {
                font-style: italic;
                text-align: center;
            }

            .cat {
                font-weight: bold;
                text-align: center;
                padding: 0.5em;
            }

            .cell {
                background-color: lightgrey;
                padding: 0.5em;
            }

            .component {
                padding-top: 0.5em;
            }
        </style>''')
        w('<table>')
        w('<tr>')
        w('<td class="from-to">from\\to</td>')
        for i in cats:
            w('<td class="cat">'); w(i); w('</td>')
        w('</tr>')
        for fro in cats:
            w('<tr>')
            w('<td class="cat">'); w(fro); w('</td>')
            for to in cats:
                style = {
                    ('audio', 'audio'): 'background-color: #ff0;',
                    ('audio+midi', 'audio'): 'background-color: #ff0;',
                    ('audio', 'midi+cmd'): 'background-color: #8f8;',
                    ('midi', 'audio'): 'background-color: #88f;',
                    ('midi', 'midi'): 'background-color: #f0f;',
                    ('midi', 'cmd'): 'background-color: #8f8;',
                    ('cmd', 'cmd'): 'background-color: #8f8;',
                    ('none', 'audio'): 'background-color: #fc4;',
                }.get((fro, to), '')
                w(f'<td class="cell" style="{style}">')
                for name, info in matrix[fro][to]:
                    w('<div class="component">')
                    i = get_short(info["in"])
                    o = get_short(info["out"])
                    w(f'{name}:<br><small>{i} -> {o}</small>')
                    w('</div>')
                w('</td>')
            w('</tr>')
        w('</table>')
        w('<div>* I/O</div>')
        w('<div>** live I/O</div>')
    webbrowser.open_new_tab(os.path.join(DIR, 'matrix.html'))

# ===== build ===== #
if args.build is not None:
    for component_path in glob.glob(os.path.join(DIR, 'components', '*')):
        component = os.path.basename(component_path)
        if args.build and component not in args.build: continue
        if component == 'base': continue
        os.chdir(component_path)
        if not os.path.exists('Cargo.toml'): continue
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
                'E501',
                'E701', 'E702', 'E704', 'E711', 'E722',
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
