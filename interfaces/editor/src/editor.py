#!/usr/bin/env python

import ctypes
import os
import StringIO
import sys
import time

HOME=os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(HOME, '..', '..', '..', 'deps', 'danssfml', 'wrapper'))
sys.path.append(os.path.join(HOME, '..', '..', '..', 'deps', 'obvious'))

from config import Controls
import media
import obvious

cpp=obvious.load_lib('Editor')
#editor
obvious.set_ffi_types(cpp.editor_init, None, str, int, str)
obvious.set_ffi_types(cpp.editor_finish)
obvious.set_ffi_types(cpp.editor_dryad_read, str)
obvious.set_ffi_types(cpp.editor_dryad_times_disconnected, int)
obvious.set_ffi_types(cpp.editor_set_text, None, str)
obvious.set_ffi_types(cpp.editor_draw)
obvious.set_ffi_types(cpp.editor_push, None, str)
obvious.set_ffi_types(cpp.editor_save, None, str)
#addable
obvious.set_ffi_types(cpp.addables_width, ctypes.c_int)
obvious.set_ffi_types(cpp.addable_at, ctypes.c_void_p, int, int)
obvious.set_ffi_types(cpp.addables_scroll, None, int)
#object
obvious.set_ffi_types(cpp.object_at, ctypes.c_void_p, int, int)
obvious.set_ffi_types(cpp.object_move_by, None, ctypes.c_void_p, int, int)
#selection
obvious.set_ffi_types(cpp.selection_add, None, ctypes.c_void_p)
obvious.set_ffi_types(cpp.selection_clear)
obvious.set_ffi_types(cpp.selection_size, int)
obvious.set_ffi_types(cpp.selection_at_index, ctypes.c_void_p, int)
obvious.set_ffi_types(cpp.selection_component, ctypes.c_void_p)
#component
obvious.set_ffi_types(cpp.component_new, None, str, str, int, int)
obvious.set_ffi_types(cpp.component_label, None, str, str)
obvious.set_ffi_types(cpp.component_phase, None, str, ctypes.c_float)
obvious.set_ffi_types(cpp.component_type, str, ctypes.c_void_p)
obvious.set_ffi_types(cpp.component_name, str, ctypes.c_void_p)
#connection
obvious.set_ffi_types(cpp.connection_new, None, str, str)
obvious.set_ffi_types(cpp.connection_del, None, str, str)
obvious.set_ffi_types(cpp.connection_command, None, str, str)
obvious.set_ffi_types(cpp.connection_midi, None, str, str)
obvious.set_ffi_types(cpp.connection_toggle, None, ctypes.c_void_p, ctypes.c_void_p)

controls=Controls(cpp)

media.set_sfml(cpp)
media.init(title='Editor')

component_types=' '.join(sorted(os.listdir(os.path.join(HOME, '..', '..', '..', 'components'))))
cpp.editor_init(sys.argv[1], int(sys.argv[2]), component_types)

class Parser:
	def __init__(self, s):
		self.s=s
		self.i=0

	def get(self, delimiter=' '):
		self.skip()
		result=''
		while True:
			c=self.s[self.i]
			if c==delimiter: break
			result+=c
			self.i+=1
		return result

	def done(self):
		self.skip()
		return self.i==len(self.s)

	def skip(self):
		while self.i<len(self.s) and self.s[self.i].isspace(): self.i+=1

class Component:
	SIZE=8

	number=1

	def __init__(self, name, type):
		cpp.component_new(name, type,
			Component.number*Component.SIZE*5,
			Component.number*Component.SIZE*5,
		)
		Component.number+=1

components={}
variables={}

while not controls.done:
	while True:
		event=media.poll_event()
		if not event: break
		controls.input(event)
	if cpp.editor_dryad_times_disconnected(): break
	while True:
		s=cpp.editor_dryad_read()
		if not s: break
		parser=Parser(s)
		while not parser.done():
			operation=parser.get()
			if operation=='add':
				name=parser.get()
				type=parser.get()
				components[name]=Component(name, type)
			elif operation=='remove':
				name=parser.get()
				del components[name]
			elif operation=='label':
				name=parser.get()
				label=parser.get()
				cpp.component_label(name, label)
			elif operation=='connect':
				src=parser.get()
				dst=parser.get()
				cpp.connection_new(src, dst)
			elif operation=='disconnect':
				src=parser.get()
				dst=parser.get()
				cpp.connection_del(src, dst)
			elif operation=='variable':
				name=parser.get('\n')
				value=parser.get('\n')
				cpp.variable_set(name, value)
			elif operation=='command':
				src=parser.get()
				dst=parser.get()
				cpp.connection_command(src, dst)
			elif operation=='midi':
				src=parser.get()
				dst=parser.get()
				cpp.connection_midi(src, dst)
			elif operation=='phase':
				name=parser.get()
				phase=ctypes.c_float(float(parser.get()))
				cpp.component_phase(name, phase)
			elif operation=='edge':
				name=parser.get()
				cpp.component_phase(name, ctypes.c_float(0))
			else: raise Exception('unknown operation "{}"'.format(operation))
	cpp.editor_draw()
	time.sleep(0.01)
