#coding: utf-8

import re, types

DEBUG=0

class AbstractControls:
	shift_table={
		'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D', 'e': 'E', 'f': 'F',
		'g': 'G', 'h': 'H', 'i': 'I', 'j': 'J', 'k': 'K', 'l': 'L',
		'm': 'M', 'n': 'N', 'o': 'O', 'p': 'P', 'q': 'Q', 'r': 'R',
		's': 'S', 't': 'T', 'u': 'U', 'v': 'V', 'w': 'W', 'x': 'X',
		'y': 'Y', 'z': 'Z',
		'1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
		'6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
		'[': '{', ']': '}', ';': ':', ',': '<', '.': '>',
		"'": '"', '/': '?', '`': '~', '=': '+', '-': '_',
		'\\': '|',
	}

	control_number=0

	def add_control(self, regex, order, mode, body):
		control_name='control_{}'.format(self.control_number)
		if DEBUG: print('control_{}: {}'.format(control_name, body))
		f='\n'.join([
			'def {0}(self, regex=r"{1}", order={2}, mode="{3}"):',
			'	"""{5}"""',
			'	{4}',
			'self.{0}=types.MethodType({0}, self)',
		]).format(
			control_name,
			regex,
			order,
			mode,
			'\n\t'.join(body),
			'\n'.join(body),
		)
		try: exec(f)
		except:
			print('-'*40)
			print(f)
			print('-'*40)
			raise
		self.control_number+=1

	def configure(self, configuration):
		mode='normal'
		order=0
		regex=None
		multiline=False
		body=[]
		for line_i, line in enumerate(configuration.splitlines()):
			if not line: continue
			#multiline body
			if multiline:
				if line.startswith(' '):
					body.append(line[1:])
					continue
				else:
					self.add_control(regex, order, mode, body)
					multiline=False
					body=[]
			#command
			split=line.split()
			if len(split)==1:
				command=split[0]
				if command=='end': continue
			if len(split)==2:
				command, value=split
				if command=='mode': mode=value; order=0; continue
				elif command=='order': order=int(value); continue
			#control
			match=re.match('([^:]*):(.*)', line)
			if not match: raise Exception('bad configuration line {}: "{}"'.format(line_i+1, line))
			regex, b=match.groups()
			if b: self.add_control(regex, order, mode, [b.strip()])
			else: multiline=True
		if body: self.add_control(regex, order, mode, body)

	def __init__(self):
		self.sequence=[]
		import collections, inspect
		D=collections.defaultdict
		self.controls=D(lambda: D(list))
		for i in dir(self):
			if i.startswith('_'): continue
			a=getattr(self, i)
			if not callable(a): continue
			if any([j not in inspect.getargspec(a).args for j in ['regex', 'order', 'mode']]): continue
			try: params=inspect.getcallargs(a)
			except: continue
			self.controls[params['order']][params['mode']].append((params['regex'], i))
		self.controls=[v for k, v in sorted(self.controls.items(), key=lambda k: k)]
		if DEBUG:
			import pprint
			for controls_order in self.controls: pprint.pprint(dict(controls_order))
		self.mode='normal'

	def input(self, word):
		self.sequence.append(word)
		def f():
			for controls_order in self.controls:
				for mode, controls_order_mode in controls_order.items():
					if not re.match(mode, self.mode): continue
					for regex, method in controls_order_mode:
						s=''.join([' '+i for i in self.sequence])
						m=re.match(regex, s)
						if DEBUG: print('{} regex◀{}▶ sequence◀{}▶ {} {}'.format(word, regex, s, method, 'MATCH' if m else ''))
						if m:
							method=getattr(self, method)
							try: method()
							except:
								print('-'*40)
								print(method.__doc__)
								print('-'*40)
								raise
							return
		f()
		self.on_input()

	def on_input(self): pass

	def clear(self): self.sequence=[]

	def reset(self): self.mode='normal'; self.clear()

	def sequence_as_text(self):
		shift=False
		r=''
		for i in self.sequence:
			c=i[1:]
			if   i[0]=='<':
				if c in self.shift_table: r+=self.shift_table[c] if shift else c
				elif c=='Space': r+=' '
				elif c[1:]=='Shift': shift=True#LShift or RShift
			elif i[0]=='>':
				if   c[1:]=='Shift': shift=False#LShift or RShift
			else: assert False
		return r
