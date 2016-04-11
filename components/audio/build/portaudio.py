import os, subprocess

os.chdir('../deps/portaudio')

if not os.path.exists('Makefile'): subprocess.check_call('./configure')
subprocess.check_call('make')
