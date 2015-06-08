#imports
import os, argparse, subprocess

#args
parser=argparse.ArgumentParser(description='run a system')
parser.add_argument('-s', action='store_true', help='skip build, just run')
parser.add_argument('-d', action='store_true', help='use debug configuration')
parser.add_argument('system', help='which system to run')
args=parser.parse_args()

#pythonpath
file_path=os.path.split(os.path.realpath(__file__))[0]
if 'PYTHONPATH' in os.environ:
	os.environ['PYTHONPATH']+=os.pathsep+file_path
else:
	os.environ['PYTHONPATH']=file_path

#config
config='Release'
if args.d: config='Debug'

#build
def shell(*args):
	cmd=' '.join(args)
	p=subprocess.Popen(cmd, shell=True)
	if p.wait(): raise subprocess.CalledProcessError(p.returncode, cmd)

if not args.s:
	if not os.path.exists('build/built'): os.makedirs('build/built')
	os.chdir('build/built')
	preamble=''
	generator=''
	if os.name=='nt':
		preamble='vcvarsall&&'
		generator='-G "NMake Makefiles"'
	shell(preamble, 'cmake', generator, '-DBUILD_SHARED_LIBS=ON', '-DCMAKE_BUILD_TYPE='+config, '..')
	shell(preamble, 'cmake --build .')
	os.chdir(file_path)

#run
os.chdir('build/built')
subprocess.check_call(['python', '-i', '../../systems/'+args.system+'.py'])
