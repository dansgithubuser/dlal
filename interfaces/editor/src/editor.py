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
cpp.editor_dryad_read.restype=ctypes.c_char_p
cpp.addable_at.restype=ctypes.c_void_p
cpp.object_at.restype=ctypes.c_void_p
cpp.object_move_by.argtypes=[ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
cpp.selection_add.argtypes=[ctypes.c_void_p]
cpp.selection_at_index.restype=ctypes.c_void_p
cpp.selection_component.restype=ctypes.c_void_p
cpp.component_type.restype=ctypes.c_char_p
cpp.component_type.argtypes=[ctypes.c_void_p]
cpp.component_name.restype=ctypes.c_char_p
cpp.component_name.argtypes=[ctypes.c_void_p]
cpp.connection_toggle.argtypes=[ctypes.c_void_p, ctypes.c_void_p]

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
