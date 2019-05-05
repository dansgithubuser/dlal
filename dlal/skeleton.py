import atexit
import collections
import ctypes
import functools
import inspect
import json
import os
import platform
import re
import subprocess
import sys
import weakref

root=os.path.join(os.path.split(os.path.realpath(__file__))[0], '..')
sys.path.append(os.path.join(root, 'deps', 'dansmidilibs'))
sys.path.append(os.path.join(root, 'deps', 'obvious'))

import midi
import obvious

def invoke(invocation):
	subprocess.check_call(invocation, shell=True)

def snake_case(camel_case):
	return re.sub('(.)([A-Z])', r'\1_\2', camel_case).lower()

def camel_case(snake_case):
	return ''.join([i.capitalize() for i in snake_case.split('_')])

def connect(*args, immediate=False):
	if len(args)<=1: return
	result=''
	for i in range(len(args)-1):
		result+=args[i].connect(args[i+1], immediate)
		if len(result): result+='\n'
	return result

class Namer:
	def __init__(self):
		self.numbers=collections.defaultdict(int)

	def name(self, component_type='c'):
		self.numbers[component_type]+=1
		if self.numbers[component_type]==1: return component_type
		return '{}{}'.format(component_type, self.numbers[component_type])
_namer=Namer()

class Skeleton:
	def __init__(self):
		self.lib=obvious.load_lib('Skeleton')
		obvious.set_ffi_types(self.lib.dlalRequest, str, str, bool)
		obvious.python_3_string_prep(self.lib)

	def _call(self, immediate, *args, sep=' '):
		def report(result):
			if   result.startswith('error'): raise RuntimeError(result)
			elif result.startswith('warning'): print(result)
			return result
		def convert(x):
			if isinstance(x, Component): return x.component
			return str(x)
		return report(self.lib.dlalRequest(
			sep.join([convert(i) for i in args]),
			immediate,
		))

	def test(self):
		return self._call(True, 'test')

	def system_build(self):
		return self._call(True, 'system/build')

	def system_switch(self, system):
		return self._call(True, 'system/switch', system)

	def system_demolish(self, system):
		return self._call(True, 'system/demolish', system)

	def system_report(self, immediate):
		return self._call(immediate, 'system/report')

	def variable_get_all(self, immediate):
		return self._call(immediate, 'variable/get')

	def variable_get(self, immediate, name):
		return self._call(immediate, 'variable/get', name)

	def variable_set(self, immediate, name, value):
		return self._call(immediate, 'variable/set', name, value, sep='\n')

	def component_get_all(self, immediate):
		return self._call(immediate, 'component/get')

	def component_get(self, immediate, name):
		return self._call(immediate, 'component/get', name)

	def component_get_connections(self, immediate):
		return self._call(immediate, 'component/get/connections')

	def component_add(self, immediate, c, slot):
		return self._call(immediate, 'component/add', c, slot)

	def component_connect(self, immediate, a, b):
		return self._call(immediate, 'component/connect', a, b)

	def component_command(self, c, immediate, *command):
		return self._call(immediate, 'component/command', c, *command)

	def component_demolish(self, c):
		return self._call(True, 'component/demolish', c)
_skeleton=Skeleton()

class ReprMethod:
	def __init__(self, target, method, **kwargs):
		self.target=weakref.ref(target)
		self.method=method
		self.kwargs=kwargs

	def __repr__(self):
		return str(getattr(self.target(), self.method)(**self.kwargs))

	def __call__(self, *args, **kwargs):
		method=getattr(self.target(), self.method)
		arg_names=inspect.getargspec(method).args
		x={k: v for k, v in self.kwargs.items() if k not in arg_names[:len(args)]}
		x.update(kwargs)
		return method(*args, **x)

class System:
	def __init__(self):
		self.system=_skeleton.system_build()
		self.switched=_skeleton.system_switch(self.system)
		self.novel_components={}
		self.set('sampleRate', 44100, True)
		self.set('samplesPerEvaluation', 128, True)
		self.l=ReprMethod(self, 'load', start=True)

	def __del__(self):
		while True:
			report=_skeleton.system_report(True)
			if not report: break
			print(report)
		_skeleton.system_switch(self.switched)
		_skeleton.system_demolish(self.system)

	def add(self, *args, **kwargs):
		slot=kwargs.get('slot', 0)
		immediate=kwargs.get('immediate', False)
		result=''
		for arg in args:
			for c in arg.get_components_to_add():
				result+=_skeleton.component_add(immediate, c, slot)
			if len(result): result+='\n'
		return result

	def set(self, name, value, immediate=False):
		_skeleton.variable_set(immediate, name, value)

	def serialize(self):
		state={}
		#variables
		state['variables']=json.loads(_skeleton.variable_get_all(immediate=True))
		#components
		components=json.loads(_skeleton.component_get_all(immediate=True))
		state['component_order']=components
		components={j: Component(
			component=_skeleton.component_get(immediate=True, name=j),
			weak=True
		) for i in components for j in i}
		state['component_types']={k: v.type(immediate=True) for k, v in components.items()}
		state['components']={
			k: re.sub('\n|\t', ' ', v.serialize(immediate=True))
			for k, v in components.items()
		}
		#connections
		state['connections']=json.loads(_skeleton.component_get_connections(immediate=True))
		#
		return json.dumps(state)

	def deserialize(self, serialized):
		state=json.loads(serialized)
		#variables
		for name, value in state['variables'].items():
			self.set(name, value, True)
		#components
		components={}
		for name, serialized in state['components'].items():
			component=component_builder(state['component_types'][name])(name=name)
			component.deserialize(serialized, immediate=True)
			components[name]=component
		for index, slot in enumerate(state['component_order']):
			for component in slot:
				component=components[component]
				self.register_novel_component(component)
				self.add(component, slot=index, immediate=True)
		#connections
		for input, output in state['connections']: components[input].connect(components[output], immediate=True)
		#
		return state

	def save(self, file_name='system.state.txt', extra={}):
		state=json.loads(self.serialize())
		state.update(extra)
		serialized=json.dumps(state, indent=2, sort_keys=True)
		with open(file_name, 'w') as file: file.write(serialized)

	def load(self, file_name='system.state.txt', start=False):
		potential_expansion=os.path.join('..', '..', 'states', file_name+'.txt')
		if os.path.exists(potential_expansion): file_name=potential_expansion
		with open(file_name) as file: state=self.deserialize(file.read())
		if start: self.start()
		return state

	def start(self):
		if not hasattr(self, 'audio'): raise Exception('no audio component')
		atexit.register(lambda: self.audio.finish(immediate=True))
		return self.audio.start(immediate=True)

	def register_novel_component(self, component):
		name=component.to_str(immediate=True)
		self.novel_components[name]=component
		if not hasattr(self, name): setattr(self, name, component)

class Component:
	_libs={}

	@staticmethod
	def from_dict(d, component_map):
		return component_map[d['component']]

	def to_dict(self): return {'component': self.to_str()}

	def set_components_to_add(self, components):
		self.components_to_add=[weakref.ref(i) for i in components]

	def get_components_to_add(self):
		return [i() for i in self.components_to_add]

	def __init__(self, component_type=None, **kwargs):
		self.component=None
		if component_type and component_type not in Component._libs:
			lib=obvious.load_lib(camel_case(component_type))
			obvious.set_ffi_types(lib.dlalBuildComponent, str, str)
			obvious.python_3_string_prep(lib)
			Component._libs[component_type]=lib
		if 'component' in kwargs:
			self.component=kwargs['component']
		else:
			self.component=Component._libs[component_type].dlalBuildComponent(
				kwargs.get('name', _namer.name(component_type))
			)
		self.weak=kwargs.get('weak', False)
		self.set_components_to_add([self])
		commands=[i.split()[0] for i in self.command('help', immediate=True).split('\n')[1:] if len(i)]
		weak_self=weakref.ref(self)
		def captain(command):
			return lambda *args, **kwargs: weak_self().command(
				*([command]+list(args)),
				immediate=kwargs.get('immediate', False),
			)
		for command in commands:
			if command not in dir(self): setattr(self, command, captain(command))

	def __del__(self):
		if self.component!=None and not self.weak:
			_skeleton.component_demolish(self)

	def transfer_component(self):
		result=self.component
		self.component=None
		return result

	def command(self, *command, immediate=False):
		return _skeleton.component_command(self, immediate, *command)

	def connect(self, output, immediate=False):
		return _skeleton.component_connect(immediate, self.output(), output)

	def output(self): return self

	def phase(self): return int(self.periodic_get().split()[1])

	def period(self): return int(self.periodic_get().split()[0])

def component_to_dict(self, members):
	result={i: getattr(self, i) for i in members}
	result={k: {'class': v.__class__.__name__, 'dict': v.to_dict()} for k, v in result.items()}
	return result

component_types={}
def inform_component_type(name, value): component_types[snake_case(name)]=value

def component_builder(component_type):
	cls=component_types.get(component_type)
	if cls: return cls
	return lambda **kwargs: Component(component_type, **kwargs)

def component_from_dict(self, members, d, component_map):
	for member in members:
		class_name=d[member]['class']
		cls=component_types.get(snake_case(class_name))
		if not cls: cls=eval(class_name)
		setattr(self, member, cls.from_dict(d[member]['dict'], component_map))

def test(): _skeleton.test()

def regularize_component_constructors(globals):
	component_dirs=sorted(os.listdir(os.path.join(root, 'components')))
	for i in component_dirs:
		if not component_types.get(i):
			globals[i.capitalize()]=functools.partial(Component, i)
