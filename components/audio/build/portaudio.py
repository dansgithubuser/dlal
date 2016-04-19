import os, subprocess

os.chdir('../deps/portaudio')

if not os.path.exists('Makefile'):
	subprocess.check_call('CFLAGS="-fPIC" ./configure --with-alsa=no --with-jack --with-oss=no --with-asihpi=no', shell=True)
subprocess.check_call('make', shell=True)
