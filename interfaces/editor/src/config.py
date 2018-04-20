from controls import AbstractControls
import re
import shlex

configuration=r'''
mode .*
order -1
.* q: self.command('quit')
.* <Backspace >Backspace:
 if self.mode=='command':
  i=0
  for i in reversed(range(len(self.sequence)-2)):
   if self.sequence[i][0]=='<': break
  self.sequence=self.sequence[:i]
 else: self.sequence=self.sequence[:-3]
end
.* x(\d+)y(\d+)$:
 self.move(
  int(match.group(1)),
  int(match.group(2)),
 )
 self.sequence=self.sequence[:-1]
end
 <Esc >Esc:
 self.reset()
 self.cpp.selection_clear()
end
.* <LShift >LShift: self.sequence=self.sequence[:-2]; self.shift=False
.* <RShift >RShift: self.sequence=self.sequence[:-2]; self.shift=False
.* <.Shift$: self.shift=True
.+ >.Shift$: self.shift=False
 >.Shift$: self.shift=False; self.clear()
order 0
.* b([<>])(\d)x(\d+)y(\d+)$:
 self.button(
  int(match.group(2)),
  match.group(1)=='<',
  int(match.group(3)),
  int(match.group(4)),
 )
 self.sequence=self.sequence[:-1]
end
.* >Esc: self.clear()
order 1
 >: self.clear()

mode normal
order 0
 <.Shift <;$:     self.mode='command'; self.clear()

mode command
 .*>Return: self.command()
'''

class Button:
	def __init__(self): self.pressed=False

	def press(self, x, y): self.x, self.y, self.pressed=x, y, True
	def release(self): self.pressed=False

	def x_to(self, x):
		dx=x-self.x
		self.x=x
		return dx
	def y_to(self, y):
		dy=y-self.y
		self.y=y
		return dy

class Controls(AbstractControls):
	def __init__(self, cpp):
		self.configure(configuration)
		AbstractControls.__init__(self)
		self.done=False
		self.shift=False
		self.command_aliases={
			'q': 'quit',
			'h': 'help',
			'w': 'write',
			'e': 'edit',
		}
		self.messaging=False
		self.cpp=cpp
		self.buttons=[Button() for _ in range(2)]

	def command(self, command=None):
		if not command: command=self.sequence_as_text()
		command=shlex.split(command)
		if not command: self.reset(); return
		name=command[0]
		name=self.command_aliases.get(name, name)
		command_name='command_'+name
		params=command[1:]
		if hasattr(self, command_name):
			try:
				result=getattr(self, command_name)(*params)
				if type(result)==str: self.message(result)
				else: self.reset()
			except Exception as e: print(e)
		else: self.message('no such command "{}"'.format(name))

	def message(self, message):
		self.reset()
		self.cpp.editor_set_text(message)
		self.messaging=True

	def button(self, button, pressed, x, y):
		if button==0:
			if pressed:
				self.buttons[0].press(x, y)
				if x>self.cpp.dans_sfml_wrapper_width()-self.cpp.addables_width():
					addable=self.cpp.addable_at(x, y)
					if addable: self.cpp.editor_push('queue_add '+self.cpp.component_type(addable))
				else:
					object=self.cpp.object_at(x, y)
					if object: self.cpp.selection_add(object)
			else: self.buttons[0].release()
		elif button==1:
			if pressed:
				connector=self.cpp.selection_component()
				connectee=self.cpp.object_at(x, y)
				if connector and connectee:
					self.cpp.connection_toggle(connector, connectee)
					self.cpp.selection_clear()

	def move(self, x, y):
		if self.buttons[0].pressed:
			dx=self.buttons[0].x_to(x);
			dy=self.buttons[0].y_to(y);
			if x>self.cpp.dans_sfml_wrapper_width()-self.cpp.addables_width(): self.cpp.addables_scroll(dy);
			else:
				for i in self.selection(): self.cpp.object_move_by(i, dx, dy)

	def selection(self):
		for i in range(self.cpp.selection_size()):
			yield self.cpp.selection_at_index(i)

	#commands
	def command_quit(self): self.done=True
	def command_pdb(self): import pdb; pdb.set_trace()
	def command_eval(self, expression): return str(eval(expression))
	def command_help(self, *args):
		if len(args)==0:
			print('help with what?')
			print('configuration')
			print('command')
		elif len(args)==1:
			if args[0]=='configuration': print('configuration:\n'+configuration)
			elif args[0]=='command':
				print('commands:')
				for i in dir(self):
					if callable(getattr(self, i)) and i.startswith('command_'): print(i[8:])
			else: print('no such help topic "{}"'.format(args[0]))
		return 'see terminal for details'
	def command_push(self, command): self.cpp.editor_push(command)
	def command_write(self, file_name):
		self.cpp.editor_save(file_name+'.editor')
	def command_edit(self, file_name):
		self.cpp.editor_load(file_name+'.editor')
	def command_name(self):
		self.cpp.editor_name()

	#callback
	def on_input(self):
		if self.messaging: self.messaging=False; return
		if   self.mode=='command': self.cpp.editor_set_text(':'+self.sequence_as_text())
		else                     : self.cpp.editor_set_text(''.join(self.sequence))
