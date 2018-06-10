import argparse
import atexit
import dlal
import os

try: input=raw_input
except: pass

parser=argparse.ArgumentParser()
parser.add_argument('file_path')
args=parser.parse_args()

#construct
system=dlal.System()
commander=dlal.Commander()
liner=dlal.Liner()
soundfont=dlal.Soundfont()
audio=dlal.Audio()

#connect
dlal.connect(liner, soundfont, audio)

#add
system.add(commander, liner, soundfont, audio)

#command
soundfont.load(os.path.join('..', '..', 'components', 'soundfont', 'deps', '32MbGMStereo.sf2'))
audio.start()
atexit.register(lambda: audio.finish())

#interface
playing=False

def play_start():
	audio.start()
	commander.queue_command(liner, 'load', args.file_path)
	global playing
	playing=True

def play_stop():
	audio.finish()
	liner.periodic_set_phase(0)
	soundfont.reset()
	global playing
	playing=False

def play_toggle():
	if not playing:
		play_start()
		return 'playing'
	else:
		play_stop()
		return 'stopped'

class ReprFunction:
	def __init__(self, function): self.function=function
	def __repr__(self): return self.function()

p=ReprFunction(play_toggle)
