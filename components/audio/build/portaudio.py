import os, subprocess

os.chdir('../deps/portaudio')

if not os.path.exists('Makefile'): subprocess.check_call('./configure --with-alsa --with-jack=no --with-oss=no --with-asihpi=no', shell=True)
subprocess.check_call('make', shell=True)
