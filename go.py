#!/usr/bin/python

import os, subprocess

#args
import argparse
parser=argparse.ArgumentParser(description='run a system')
parser.add_argument('--run-only', '-r', action='store_true', help='skip build, just run')
parser.add_argument('--debug', '-d', action='store_true', help='use debug configuration')
parser.add_argument('--test', '-t', help='run tests specified by glob')
parser.add_argument('--system', '-s', help='which system to run')
parser.add_argument('--interface', '-i', action='append', help='interface:port')
args=parser.parse_args()

#helpers
def shell(*args): p=subprocess.check_call(' '.join(args), shell=True)

#current directory
file_path=os.path.split(os.path.realpath(__file__))[0]
os.chdir(file_path)
built_rel_path=os.path.join('build', 'built')

#pythonpath
if 'PYTHONPATH' in os.environ:
	os.environ['PYTHONPATH']+=os.pathsep+file_path
else:
	os.environ['PYTHONPATH']=file_path

#config
config='Release'
if args.debug: config='Debug'

#build
if not args.run_only:
	if not os.path.exists(built_rel_path): os.makedirs(built_rel_path)
	os.chdir(built_rel_path)
	preamble=''
	generator=''
	if os.name=='nt':
		preamble='vcvarsall&&'
		generator='-G "NMake Makefiles"'
	shell(preamble, 'cmake', generator, '-DBUILD_SHARED_LIBS=ON', '-DCMAKE_BUILD_TYPE='+config, '..')
	shell(preamble, 'cmake --build .')
	os.chdir(file_path)

#library path
os.environ['LD_LIBRARY_PATH']=os.path.join(file_path, 'build', 'built')

#test
if args.test:
	#setup
	import glob, sys
	tests=[os.path.realpath(x) for x in glob.glob(os.path.join('tests', args.test))]
	overall=0
	print('RUNNING TESTS')
	#loop over tests
	for test in tests:
		#run test
		os.chdir(built_rel_path)
		r=subprocess.call(['python', os.path.join(test, 'test.py')])
		os.chdir(file_path)
		#read result and expected
		def read(file_name):
			with open(file_name) as file: contents=file.read()
			return [float(x) for x in contents.split()]
		raw=read(os.path.join('build', 'built', 'raw.txt'))
		expected=read(os.path.join(test, 'expected.txt'))
		#compare result to expected
		if len(raw)!=len(expected): r=1
		else:
			for i in range(len(raw)):
				if abs(raw[i]-expected[i])>0.00001:
					r=1
		#report
		overall|=r
		print('-' if r else '+', os.path.split(test)[1])
	#finish
	if overall:
		print('TESTS HAVE FAILED!')
		sys.exit(-1)
	print('ALL TESTS SUCCEEDED')

#interfaces
if args.interface:
	def find_binary(name):
		for root, dirs, files in os.walk('.'):
			for file in files:
				import re
				if re.match(name.lower()+r'(\.exe)?$', file.lower()):
					return os.path.join(root, file)
	if not args.run_only:
		for i in args.interface:
			name, port=i.split(':')
			os.chdir(os.path.join('interfaces', name, 'build'))
			shell('cmake .')
			shell('cmake --build .')
			os.chdir(file_path)
	for i in args.interface:
		name, port=i.split(':')
		os.chdir(os.path.join('interfaces', name, 'build'))
		p=subprocess.Popen([find_binary(name), '127.0.0.1', port])
		import atexit
		atexit.register(lambda: p.kill())
		os.chdir(file_path)

#run
if args.system:
	os.chdir(built_rel_path)
	shell('python', '-i', os.path.join('..', '..', 'systems', args.system+'.py'))
	os.chdir(file_path)

#done
print('all requests processed; call with -h for help')
