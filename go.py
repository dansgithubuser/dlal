#!/usr/bin/env python

import glob
import http.server
import os
import platform
import socketserver
import subprocess
import sys
import webbrowser

assert sys.version_info.major == 3

# args
import argparse
parser = argparse.ArgumentParser(description='interface for developer operations')
parser.add_argument('--setup', action='store_true', help='install dependencies')
parser.add_argument('--build', '-b', action='store_true', help='build')
parser.add_argument('--build-update-submodules', action='store_true')
parser.add_argument('--test', '-t', help='run tests specified by glob')
parser.add_argument('--test-runs', '--tr', help='custom number of runs for testing', default=10)
parser.add_argument('--system', '-s', help='which system to run (? to list systems)')
parser.add_argument('--system-arguments', '--sa', default='-g', help='arguments to pass to system (default -g)')
parser.add_argument('--interface', '-i', action='store_true', help='open web interface and start server')
parser.add_argument('--debug', '-d', action='store_true', help='use debug configuration')
parser.add_argument('--can', '-c', help='canned commands (? for help)')
parser.add_argument('--python', default='python')
if len(sys.argv) == 1:
    parser.print_help()
    sys.exit()
args = parser.parse_args()

print('-- python --')
print(sys.version)
print('------------')

# canned commands
if args.can:
    canned_commands = {
        'b': '-s soundboard',
        'f': '-s sonic     ',
        's': '-s soundfont ',
        'v': '-s vst       ',
        'l': '-s loader',
    }
    canned_options = {
        'b': '-b',
        'd': '-d',
    }
    import pprint
    if args.can == '?':
        print('usage: `can.options.state`')
        print('available cans:')
        pprint.pprint(canned_commands)
        print('available options:')
        pprint.pprint(canned_options)
        print('available states:')
        pprint.pprint([i[:-4] for i in os.listdir('states') if i.endswith('.txt')])
        sys.exit(0)
    can = args.can.split('.')
    name = can[0]
    options = can[1] if len(can) > 1 else ''
    system_state = can[2] if len(can) > 2 else None
    if name not in canned_commands:
        print('invalid command -- valid commands are')
        pprint.pprint(canned_commands)
        sys.exit(1)
    command = canned_commands[name]
    if type(command) == str:
        command = command.split()
    for i in options:
        if i not in canned_options:
            print('invalid option "{0}" -- valid options are'.format(i))
            pprint.pprint(canned_options)
            continue
        option = canned_options[i]
        if type(option) == str:
            option = option.split()
        command += option
    if system_state:
        command += ['--sa', '-l {} -g'.format(system_state)]
    args = parser.parse_args(command)

# helpers
def shell(*args):
    invocation = ' '.join(args)
    print('invoking `{}` in {}'.format(invocation, os.getcwd()))
    subprocess.check_call(invocation, shell=True)

# current directory
file_path = os.path.split(os.path.realpath(__file__))[0]
os.chdir(file_path)
built_rel_path = os.path.join('build', 'built')

# pythonpath
if 'PYTHONPATH' in os.environ:
    os.environ['PYTHONPATH'] += os.pathsep + file_path
else:
    os.environ['PYTHONPATH'] = file_path

# config
config = 'Release'
if args.debug:
    config = 'Debug'

# setup
if args.setup:
    if platform.system() == 'Linux':
        # sfml dependencies
        shell('sudo apt install --yes --force-yes '
            'libxcb-image0-dev '
            'freeglut3-dev '
            'libjpeg-dev '
            'libfreetype6-dev '
            'libxrandr-dev '
            'libglew-dev '
            'libsndfile1-dev '
            'libopenal-dev '
            'libudev-dev '
        )
        # tkinter
        shell('sudo apt install --yes --force-yes python3-tk')
        # rtmidi dependencies
        shell('sudo apt install --yes --force-yes libasound2-dev')
        # cmake
        shell('wget http://www.cmake.org/files/v3.2/cmake-3.2.3-Linux-x86_64.sh')
        shell('chmod a+x cmake-3.2.3-Linux-x86_64.sh')
        shell('sudo ./cmake-3.2.3-Linux-x86_64.sh --skip-license --prefix=/usr/local')
    elif platform.system() == 'Darwin':
        shell('brew update')
        shell('brew uninstall --force cmake')
        shell('brew install cmake')
    else:
        print('unrecognized system ' + platform.system())
        sys.exit(1)
    sys.exit(0)

# build
if args.build:
    if args.build_update_submodules: shell('git submodule update --init --recursive')
    if not os.path.exists(built_rel_path):
        os.makedirs(built_rel_path)
    os.chdir(built_rel_path)
    preamble = ''
    generator = ''
    shell('cmake --version')
    shell(preamble, 'cmake', generator, '-DBUILD_SHARED_LIBS=ON', '-DCMAKE_BUILD_TYPE=' + config, '..')
    invocation = 'cmake --build . --config ' + config
    if platform.system() != 'Darwin':
        invocation += ' --target install'
    shell(preamble, invocation)
    import shutil
    for path, folders, files in os.walk('installed'):
        for file in files:
            if file in ['openal32.dll']:
                src = os.path.join(path, file)
                dst = os.path.join(file)
                print('{} ---> {}'.format(os.path.abspath(src), os.path.abspath(dst)))
                shutil.copyfile(src, dst)
    os.chdir(file_path)

# library path
os.environ['LD_LIBRARY_PATH'] = os.path.join(file_path, 'build', 'built')

# test
if args.test:
    # setup
    tests = [os.path.realpath(x) for x in glob.glob(os.path.join('tests', args.test))]
    overall = True
    report = []
    print('RUNNING TESTS')
    # loop over tests
    for test in tests:
        runs = int(args.test_runs)
        successes = 0
        for i in range(runs):
            # run test
            os.chdir(built_rel_path)
            r = subprocess.call([args.python, os.path.join(test, 'test.py')])
            os.chdir(file_path)
            if not r:
                # read result and expected
                def read(file_name):
                    with open(file_name) as file:
                        contents = file.read()
                    return [float(x) for x in contents.split()]
                raw = read(os.path.join('build', 'built', 'raw.txt'))
                expected = read(os.path.join(test, 'expected.txt'))
                # compare result to expected
                if len(raw) != len(expected):
                    r = 1
                else:
                    def bad(i): return abs(raw[i]-expected[i]) > 0.00001
                    for i in range(len(raw)):
                        if bad(i):
                            r = 1
                    if r:
                        for i in range(len(raw)):
                            print('{} {} {}'.format(raw[i], expected[i], '!' if bad(i) else ''))
            else:
                print('abnormal return code {}'.format(r))
            # bookkeepping
            if r:
                overall = False
            else:
                successes += 1
            print('{}{}'.format('-' if r else '+', os.path.split(test)[1]))
        report.append('{:3}/{} {}'.format(successes, runs, os.path.split(test)[1]))
    # finish
    for i in report:
        print(i)
    if not overall:
        print('TESTS HAVE FAILED!')
        sys.exit(1)
    print('ALL TESTS SUCCEEDED')

# interface
if args.interface:
    webbrowser.open_new_tab('http://localhost:8000/web/index.html')
    with socketserver.TCPServer(('', 8000), http.server.SimpleHTTPRequestHandler) as httpd:
        httpd.serve_forever()

# run
os.chdir(built_rel_path)
if args.system:
    systems_path = os.path.join('..', '..', 'systems')
    system_path = os.path.join(systems_path, args.system + '.py')
    if os.path.exists(system_path):
        shell(args.python, '-i', system_path, *args.system_arguments.split())
    else:
        print('available systems are:')
        for i in glob.glob(os.path.join('..', '..', 'systems', '*.py')):
            print(os.path.split(i)[-1][:-3])
