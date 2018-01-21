from controls import AbstractControls
import re

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
 self.cpp.editor_move(
  int(match.group(1)),
  int(match.group(2)),
 )
 self.sequence=self.sequence[:-1]
end
 <Esc >Esc: self.reset()
.* <LShift >LShift: self.sequence=self.sequence[:-2]; self.shift=False
.* <RShift >RShift: self.sequence=self.sequence[:-2]; self.shift=False
.* <.Shift$: self.shift=True
.+ >.Shift$: self.shift=False
 >.Shift$: self.shift=False; self.clear()
order 0
.* b([<>])(\d)x(\d+)y(\d+)$:
 self.cpp.editor_button(
  int(match.group(2)),
  1 if match.group(1)=='<' else 0,
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

class Controls(AbstractControls):
	def __init__(self, cpp):
		self.configure(configuration)
		AbstractControls.__init__(self)
		self.done=False
		self.shift=False
		self.command_aliases={
			'q': 'quit',
			'h': 'help',
		}
		self.messaging=False
		self.cpp=cpp

	def command(self, command=None):
		if not command: command=self.sequence_as_text()
		command=command.split()
		if not command: self.reset(); return
		name=command[0]
		self.force=False
		if name.endswith('!'): self.force=True; name=name[:-1]
		name=self.command_aliases.get(name, name)
		command_name='command_'+name
		params=command[1:]
		if hasattr(self, command_name):
			result=getattr(self, command_name)(*params)
			if type(result)==str: self.message(result)
			else: self.reset()
		else: self.message('no such command "{}"'.format(name))

	def message(self, message):
		self.reset()
		self.cpp.editor_set_text(message)
		self.messaging=True

	#commands
	def command_quit(self): self.done=True
	def command_pdb(self): import pdb; pdb.set_trace()
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

	#callback
	def on_input(self):
		if self.messaging: self.messaging=False; return
		if   self.mode=='command': self.cpp.editor_set_text(':'+self.sequence_as_text())
		else                     : self.cpp.editor_set_text(''.join(self.sequence))
