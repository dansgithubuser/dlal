from .skeleton import *

try: import tkinter
except ImportError: import Tkinter as tkinter

class Fir(Component):
	def __init__(self):
		Component.__init__(self, 'fir')
		self.commander=Component('commander')
		self.commander.connect(self)
		self.components_to_add=[self.commander, self]

	def show_controls(self, title='dlal formant synth controls'):
		root=tkinter.Tk(title)
		root.title()
		tkinter.Label(text='frequency 1').grid(row=0, column=0)
		tkinter.Label(text='magnitude 1').grid(row=0, column=1)
		tkinter.Label(text='width 1'    ).grid(row=0, column=2)
		tkinter.Label(text='frequency 2').grid(row=0, column=3)
		tkinter.Label(text='magnitude 2').grid(row=0, column=4)
		tkinter.Label(text='width 2'    ).grid(row=0, column=5)
		f1f=tkinter.Scale(command=lambda x: self.live_command('formant 0 {} {} {} 0.5'.format(f1f.get(), f1m.get(), f1w.get())))
		f1m=tkinter.Scale(command=lambda x: self.live_command('formant 0 {} {} {} 0.5'.format(f1f.get(), f1m.get(), f1w.get())))
		f1w=tkinter.Scale(command=lambda x: self.live_command('formant 0 {} {} {} 0.5'.format(f1f.get(), f1m.get(), f1w.get())))
		f2f=tkinter.Scale(command=lambda x: self.live_command('formant 1 {} {} {} 0.5'.format(f2f.get(), f2m.get(), f2w.get())))
		f2m=tkinter.Scale(command=lambda x: self.live_command('formant 1 {} {} {} 0.5'.format(f2f.get(), f2m.get(), f2w.get())))
		f2w=tkinter.Scale(command=lambda x: self.live_command('formant 1 {} {} {} 0.5'.format(f2f.get(), f2m.get(), f2w.get())))
		f1f.config(from_=10000, to=0, length=600)
		f1m.config(from_=    1, to=0, length=600, resolution=0.001)
		f1w.config(from_=10000, to=0, length=600)
		f2f.config(from_=10000, to=0, length=600)
		f2m.config(from_=    1, to=0, length=600, resolution=0.001)
		f2w.config(from_=10000, to=0, length=600)
		f1f.grid(row=1, column=0)
		f1m.grid(row=1, column=1)
		f1w.grid(row=1, column=2)
		f2f.grid(row=1, column=3)
		f2m.grid(row=1, column=4)
		f2w.grid(row=1, column=5)

	phonetics={
		'q': 'a as in father',
		'w': 'u as in tube',
		'e': 'e as in bet',
		'y': 'ee as in eel',
		'u': 'u as in cup',
		'i': 'i as in indigo (IPA I)',
		'o': 'o as in rode',
		'a': 'a as in apple',
		'x': 'oo as in foot',
		'c': 'a as in pay',
		'r': 'r as in ray',
		'l': 'l as in lay',
		'm': 'm as in may',
		'n': 'n as in need',
		',': 'ng as in sing (IPA velar nasal)',
		's': 's as in seven',
		'z': 'z as in zebra',
		'f': 'f as in fine',
		'v': 'v as in very',
		'.': 'th as in thanks (IPA theta)',
		'/': 'th as in the (IPA voiced dental fricative)',
		';': 'sh as in she (IPS S)',
		"'": 's as in fusion (IPA 3)',
		't': 't as in time',
		'd': 'd as in dime',
		'k': 'k as in kite',
		'g': 'g as in get',
		'p': 'p as in pet',
		'b': 'b as in bet',
		'[': 'ch as in check (IPA tS)',
		'j': 'j as in jet (IPA d3)',
		'h': 'h as in hat',
	}

	stops='tdkgpb[j'
	voiced="qweyuioaxcrlmn,zv/'dgb"

	formants_voice=2
	phonetics_voice={
		'q': [( 750, 1.0), (1000, 0.3)],
		'w': [( 315, 1.0), ( 790, 0.3)],
		'e': [( 650, 1.0), (1550, 0.6)],
		'y': [( 350, 1.0), (2500, 0.5)],
		'u': [( 650, 1.0), (1110, 0.4)],
		'i': [( 350, 1.0), (1750, 0.4)],
		'o': [( 550, 1.0), ( 800, 0.3)],
		'a': [( 900, 1.0), (1600, 0.3)],
		'x': [( 540, 1.0), (1210, 0.6)],
		'c': [( 550, 1.0), (1900, 0.2)],
		'r': [( 390, 1.0), (1400, 0.4)],
		'l': [( 390, 1.0), ( 800, 0.3)],
		'm': [( 200, 1.0), (2000, 0.3)],
		'n': [( 230, 1.0), (2200, 0.3)],
		',': [( 230, 1.0), (2400, 0.4)],
		'z': [( 200, 1.0), (1300, 0.3)],
		'v': [( 200, 1.0), (1100, 0.3)],
		'/': [( 200, 1.0), (1300, 0.3)],
		"'": [( 200, 1.0), (1300, 0.3)],
		'j': [( 230, 1.0), (2200, 0.3)],
	}

	def phonetic_voice(self, p):
		if p in Fir.stops and p in Fir.voiced:
			pass
		elif p not in Fir.phonetics_voice:
			for i in range(Fir.formants_voice):
				self.live_command('formant_mute {} 0.1'.format(i))
		else:
			p=Fir.phonetics_voice[p]
			for i in range(len(p)):
				self.live_command('formant {} {} {} 10000 0.1'.format(i, p[i][0], p[i][1]))

	formants_noise=2
	phonetics_noise={
		's': [[ 3000, 0.500, 1e4, 0.10], [    0, 0.000, 1e4, 0.10]],
		'z': [[ 3000, 0.250, 1e4, 0.10], [    0, 0.000, 1e4, 0.10]],
		'f': [[ 8000, 1.000, 1e4, 0.10], [    0, 0.000, 1e4, 0.10]],
		'v': [[ 8000, 1.000, 1e4, 0.10], [    0, 0.000, 1e4, 0.10]],
		'.': [[ 7000, 1.000, 1e4, 0.10], [    0, 0.000, 1e4, 0.10]],
		'/': [[ 7000, 1.000, 1e4, 0.10], [    0, 0.000, 1e4, 0.10]],
		';': [[    0, 0.100, 1e4, 0.10], [ 1000, 0.300, 1e4, 0.10]],
		"'": [[    0, 0.050, 1e4, 0.10], [ 1000, 0.150, 1e4, 0.10]],
		't': [[    0, 0.100, 1e6, 0.10], [ 4000, 1.000, 1e6, 0.10]],
		'd': [[    0, 0.050, 1e6, 0.10], [ 2000, 0.500, 1e6, 0.10]],
		'k': [[    0, 0.500, 1e6, 0.10], [  500, 0.500, 1e3, 0.10]],
		'g': [[    0, 0.500, 1e6, 0.10], [  500, 0.500, 1e3, 0.10]],
		'p': [[    0, 0.500, 1e6, 0.20], [    0, 0.500, 1e4, 0.20]],
		'b': [[    0, 0.250, 1e6, 0.20], [    0, 0.250, 1e4, 0.20]],
		'[': [[ 4000, 0.400, 1e6, 0.10], [ 1000, 0.500, 1e5, 0.00]],
		'j': [[ 4000, 0.200, 1e6, 0.10], [ 1000, 0.250, 1e5, 0.00]],
		'h': [[  650, 0.500, 1e4, 0.10], [ 1110, 0.200, 1e4, 0.10]],
	}

	def phonetic_noise(self, p):
		if p not in Fir.phonetics_noise:
			for i in range(Fir.formants_noise):
				self.live_command('formant_mute {} 0.1'.format(i))
		elif p in Fir.stops:
			p=Fir.phonetics_noise[p]
			for i in range(Fir.formants_noise):
				self.live_command('formant {} {} {} {} 1'.format(i, p[i][0], p[i][1], p[i][2]))
				self.live_command('formant_mute {} {}'.format(i, p[i][3]))
		else:
			p=Fir.phonetics_noise[p]
			for i in range(Fir.formants_noise):
				self.live_command('formant {} {} {} {} 1'.format(i, p[i][0], p[i][1], p[i][2]))

	def live_command(self, command):
		self.commander.command('queue 0 0 '+command)
