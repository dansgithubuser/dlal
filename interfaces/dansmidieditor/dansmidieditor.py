try:
	import sdl2
except:
	print('I need to install pysdl2. Enter y if this is OK.')
	try: input=raw_input
	except: pass
	if input()!='y': raise Exception('user disallowed installation of sdl2')
	import subprocess
	subprocess.check_call('sudo pip install pysdl2', shell=True)

import sdl2, sdl2.ext
import sys, time

sdl2.ext.init()
window=sdl2.ext.Window("dan's midi editor", size=(800, 600))
window.show()

renderer=sdl2.ext.Renderer(window)

while True:
	for event in sdl2.ext.get_events():
		if event.type==sdl2.SDL_QUIT:
			sys.exit()
		elif event.type==sdl2.SDL_KEYDOWN:
			print('keydown    : {}'.format(event.key.keysym.sym))
		elif event.type==sdl2.SDL_KEYUP:
			print('keyup      : {}'.format(event.key.keysym.sym))
		elif event.type==sdl2.SDL_MOUSEMOTION:
			print('motion     : {} {} {} {}'.format(event.motion.x, event.motion.y, event.motion.xrel, event.motion.yrel))
		elif event.type==sdl2.SDL_MOUSEBUTTONDOWN:
			print('button down: {} {} {}'.format(event.button.button, event.button.x, event.button.y))
		elif event.type==sdl2.SDL_MOUSEBUTTONUP:
			print('button up  : {} {} {}'.format(event.button.button, event.button.x, event.button.y))
		elif event.type==sdl2.SDL_MOUSEWHEEL:
			print('wheel      : {}'.format(event.wheel.y))
	renderer.clear()
	renderer.fill([[0, 0, 10, 20]])
	renderer.present()
	window.refresh()
	time.sleep(0.01)
