#!/usr/bin/env python

#=====ensure sdl2 is installed=====#
try:
	import sdl2
except:
	print('I need to install pysdl2. Enter y if this is OK.')
	if input()!='y': raise Exception('user disallowed installation of sdl2')
	import subprocess
	subprocess.check_call('sudo pip install pysdl2', shell=True)

#=====setup general=====#
import sdl2, sdl2.ext
import sys, time

sdl2.ext.init()
window=sdl2.ext.Window("dan's midi editor", size=(800, 600))
window.show()

renderer=sdl2.ext.Renderer(window)

#=====setup controls=====#
class Latches:
	def __init__(self):
		import collections
		self.latches=collections.defaultdict(bool)

	def latch(self, x):
		if self.latches[x]: return False
		self.latches[x]=True
		return True

	def unlatch(self, x):
		if not self.latches[x]: return False
		del self.latches[x]
		return True

latches=Latches()

def sym_to_morpheme(sym):
	import string
	if sym in [ord(i) for i in string.ascii_letters+string.digits+string.punctuation]: return chr(sym)
	if sym==27: return 'esc'
	if sym==13: return 'enter'
	return '({})'.format(sym)

from config import controls

#=====main loop=====#
while not controls.done:
	for event in sdl2.ext.get_events():
		if event.type==sdl2.SDL_QUIT:
			controls.input('q')
		elif event.type==sdl2.SDL_KEYDOWN:
			x=sym_to_morpheme(event.key.keysym.sym)
			if latches.latch('k'+x): controls.input('<'+x)
		elif event.type==sdl2.SDL_KEYUP:
			x=sym_to_morpheme(event.key.keysym.sym)
			if latches.unlatch('k'+x): controls.input('>'+x)
		elif event.type==sdl2.SDL_MOUSEMOTION:
			controls.input('x{}y{}dx{}dy{}'.format(event.motion.x, event.motion.y, event.motion.xrel, event.motion.yrel))
		elif event.type==sdl2.SDL_MOUSEBUTTONDOWN:
			x=str(event.button.button)
			if latches.latch('b'+x): controls.input('b+{}x{}y{}'.format(x, event.button.x, event.button.y))
		elif event.type==sdl2.SDL_MOUSEBUTTONUP:
			x=str(event.button.button)
			if latches.unlatch('b'+x): controls.input('b-{}x{}y{}'.format(x, event.button.x, event.button.y))
		elif event.type==sdl2.SDL_MOUSEWHEEL:
			controls.input('w{}'.format(event.wheel.y))
	renderer.clear()
	controls.view.draw(renderer)
	renderer.present()
	window.refresh()
	time.sleep(0.01)
