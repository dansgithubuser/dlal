#!/usr/bin/env python3

import argparse
import collections
import datetime
import glob
import os
import pprint
import re
import shutil
import signal
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
parser.add_argument('--component-new', '--cn', nargs='+', metavar=('name', 'readme'))
parser.add_argument('--component-info', '--ci')
parser.add_argument('--component-base-docs', '--cbd', action='store_true')
parser.add_argument('--component-matrix', '--cm', action='store_true')
parser.add_argument('--build', '-b', action='store_true')
parser.add_argument('--build-snoop', '--bs', choices=['command', 'midi', 'audio'], nargs='+', default=[])
parser.add_argument('--interact', '-i', action='store_true', help='run interactive Python with dlal imported, can be paired with --run')
parser.add_argument('--run', '-r', nargs=argparse.REMAINDER, help='run specified system, optionally with args')
parser.add_argument('--debug', '-d', action='store_true', help='run with debug logs on')
parser.add_argument('--deploy', nargs=3, metavar=('user', 'host', 'path'), help="rsync what's needed to run to specified destination")
parser.add_argument('--style-check', '--style', action='store_true')
parser.add_argument('--style-rust-fix', action='store_true')
args = parser.parse_args()

DIR = os.path.dirname(os.path.realpath(__file__))

def blue(text):
    return '\x1b[34m' + text + '\x1b[0m'

def timestamp():
    return '{:%Y-%m-%d %H:%M:%S.%f}'.format(datetime.datetime.now())

def invoke(
    *args,
    quiet=False,
    env_add={},
    env_add_secrets=set(),
    handle_sigint=True,
    popen=False,
    check=True,
    put_in=False,
    get_out=False,
    get_err=False,
    **kwargs,
):
    if len(args) == 1 and type(args[0]) == str:
        args = args[0].split()
    if not quiet:
        print(blue('-'*40))
        print(timestamp())
        print(os.getcwd()+'$', end=' ')
        if any([re.search(r'\s', i) for i in args]):
            print()
            for i in args: print(f'\t{i} \\')
        else:
            for i, v in enumerate(args):
                if i != len(args)-1:
                    end = ' '
                else:
                    end = ';\n'
                print(v, end=end)
        if env_add:
            print('env_add:', {k: (v if k not in env_add_secrets else '...') for k, v in env_add.items()})
        if kwargs: print(kwargs)
        if popen: print('popen')
        print()
    if env_add:
        env = os.environ.copy()
        env.update(env_add)
        kwargs['env'] = env
    if put_in and 'stdin' not in kwargs: kwargs['stdin'] = subprocess.PIPE
    if get_out: kwargs['stdout'] = subprocess.PIPE
    if get_err: kwargs['stderr'] = subprocess.PIPE
    p = subprocess.Popen(args, **kwargs)
    if handle_sigint:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
    if put_in:
        if type(put_in) == str:
            put_in = put_in.encode()
        p.stdin.write(put_in)
        if popen:
            p.stdin.flush()
        else:
            p.stdin.close()
    if popen:
        return p
    stdout, stderr = p.communicate()
    p.out = stdout
    p.err = stderr
    if handle_sigint:
        signal.signal(signal.SIGINT, signal.SIG_DFL)
    if check and p.returncode:
        raise Exception(f'invocation {repr(args)} returned code {p.returncode}.')
    if get_out:
        stdout = stdout.decode('utf-8')
        if get_out != 'exact': stdout = stdout.strip()
        if not get_err: return stdout
    if get_err:
        stderr = stderr.decode('utf-8')
        if get_err != 'exact': stderr = stderr.strip()
        if not get_out: return stderr
    if get_out and get_err: return stdout, stderr
    return p

# ===== skeleton ===== #
os.chdir(os.path.join(DIR, 'skeleton'))

if args.venv_freshen:
    shutil.rmtree('venv', ignore_errors=True)
    invoke('python3', '-m', 'venv', 'venv')

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
use dlal_component_base::{component, json, serde_json, Body, CmdResult};

component!(
    {"in": ["?"], "out": ["?"]},
    [
        "run_size",
        "sample_rate",
        //{"name": "join_info"},
        //"audio",
        "uni",
        //"multi",
        //"check_audio",
        //{"name": "connect_info"},
        //{"name": "disconnect_info"},
        //{"name": "field_helpers", "fields": ["value1"], "kinds": ["rw", "json"]},
    ],
    {
        value1: f32,
        value2: f32,
    },
    {
        "value2": {
            "args": [{"name": "value2", "optional": true}],
        },
    },
);

impl ComponentTrait for Component {
    fn init(&mut self) {
        self.value1 = 1.0;
        self.value2 = 2.0;
    }

    fn run(&mut self) {
    }

    fn midi(&mut self, msg: &[u8]) {
    }

    fn audio(&mut self) -> Option<&mut [f32]> {
        None
    }

    fn join(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(None)
    }

    fn connect(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(None)
    }

    fn disconnect(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(None)
    }

    fn to_json_cmd(&mut self, _body: serde_json::Value) -> CmdResult {
        Ok(Some(field_helper_to_json!(self, {
            "value2": self.value2,
        })))
        //Ok(Some(json!({
        //    "value1": self.value1,
        //    "value2": self.value2,
        //})))
    }

    fn from_json_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        let j = field_helper_from_json!(self, body);
        //let j = body.arg::<serde_json::Value>(0)?;
        //self.value1 = j.at("value1")?;
        self.value2 = j.at("value2")?;
        Ok(None)
    }
}

impl Component {
    fn value2_cmd(&mut self, body: serde_json::Value) -> CmdResult {
        if let Ok(v) = body.arg(0) {
            self.value2 = v;
        }
        Ok(Some(json!(self.value2)))
    }
}
'''

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
        del command['name']
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
if args.build:
    for i in args.build_snoop:
        os.environ[f'DLAL_SNOOP_{i.upper()}'] = '1'
    os.chdir(os.path.join(DIR, 'components'))
    invoke('cargo build --release', env_add={'PORTAUDIO_ONLY_STATIC': '1'})

# ===== interact & run ===== #
if args.interact or args.run:
    os.chdir(os.path.join(DIR))
    if 'PYTHONPATH' in os.environ:
        os.environ['PYTHONPATH'] += os.pathsep + os.path.join(DIR, 'skeleton')
    else:
        os.environ['PYTHONPATH'] = os.path.join(DIR, 'skeleton')
    if args.debug:
        os.environ['DLAL_LOG_LEVEL'] = 'debug'
    if args.run:
        invocation = ['python3']
        if args.interact:
            invocation.append('-i')
        invocation.extend(args.run)
        invocation = ' '.join(invocation)
    else:
        invocation = 'python3 -i -c "import dlal"'
    p = subprocess.Popen(invocation, shell=True)
    signal.signal(signal.SIGINT, lambda *args: p.send_signal(signal.SIGINT))
    p.wait()

# ===== deploy ===== #
if args.deploy:
    os.chdir(DIR)
    user, host, dst = args.deploy
    globs = [
        'assets',
        'components/target/release/*.so',
        'deps',
        'do.py',
        'requirements.txt',
        'skeleton',
        'systems',
        'venv-on',
        'venv-off',
        'web',
    ]
    print('Invocations will look like:')
    print(f'rsync -r assets {user}@{host}:{dst}/assets')
    print('Does this seem right? Enter to continue, ctrl-c to abort.')
    input()
    for i in globs:
        for path in glob.glob(i):
            if os.path.isdir(path):
                path = f'{path}/'
            invoke(f'ssh {user}@{host} mkdir -p {dst}/{os.path.dirname(path)}', quiet=True)
            invoke(f'rsync -r {path} {user}@{host}:{dst}/{path}')

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
                'W503', 'W504',
                'E124', 'E128', 'E131',
                'E203', 'E226',
                'E301', 'E302', 'E305', 'E306',
                'E402',
                'E501',
                'E701', 'E702', 'E704', 'E711', 'E712', 'E722',
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
