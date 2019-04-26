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

_systems=0

def report(text):
	t=ctypes.cast(text, ctypes.c_char_p).value.decode('utf-8')
	_skeleton.dlalFree(text)
	if   t.startswith('error'): raise RuntimeError(t)
	elif t.startswith('warning'): print(t)
	return t

def connect(*args):
	if len(args)<=1: return
	result=''
	for i in range(len(args)-1):
		result+=args[i].connect(args[i+1])
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

_skeleton=obvious.load_lib('Skeleton')
obvious.set_ffi_types(_skeleton.dlalDemolishComponent, None, ctypes.c_void_p)
obvious.set_ffi_types(_skeleton.dlalDyadInit)
obvious.set_ffi_types(_skeleton.dlalDyadShutdown)
obvious.set_ffi_types(_skeleton.dlalBuildSystem, ctypes.c_void_p, int)
obvious.set_ffi_types(_skeleton.dlalDemolishSystem, None, ctypes.c_void_p)
obvious.set_ffi_types(_skeleton.dlalReport, None, ctypes.c_void_p, ctypes.c_char_p)
obvious.set_ffi_types(_skeleton.dlalComponentWithName, ctypes.c_void_p, ctypes.c_void_p, str)
obvious.set_ffi_types(_skeleton.dlalRename, None, ctypes.c_void_p, ctypes.c_void_p, str)
obvious.set_ffi_types(_skeleton.dlalSetVariable, ctypes.c_void_p, ctypes.c_void_p, str, str)
obvious.set_ffi_types(_skeleton.dlalCommand, ctypes.c_void_p, ctypes.c_void_p, str)
obvious.set_ffi_types(_skeleton.dlalAdd, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint)
obvious.set_ffi_types(_skeleton.dlalConnect, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
obvious.set_ffi_types(_skeleton.dlalDisconnect, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
obvious.set_ffi_types(_skeleton.dlalSystem, ctypes.c_void_p, ctypes.c_void_p)
obvious.set_ffi_types(_skeleton.dlalSerialize, ctypes.c_void_p, ctypes.c_void_p)
obvious.set_ffi_types(_skeleton.dlalFree, None, ctypes.c_void_p)
obvious.set_ffi_types(_skeleton.dlalTest)

TextCallback=ctypes.CFUNCTYPE(None, ctypes.c_char_p)

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
	def __init__(self, port=None):
		global _systems
		if _systems==0:
			_skeleton.dlalDyadInit()
		if port==None:
			if _systems==0:
				port=9088
			else:
				port=0
		_systems+=1
		weak_self=weakref.ref(self)
		def handler(command):
			command=command.split()
			if len(command)<4: return
			if command[0]!='2': return
			def queue_add():
				component=component_builder(command[4])()
				weak_self().register_novel_component(component)
				weak_self().add(component)
			def queue_connect():
				connector=component_with_name(weak_self(), command[4])
				connectee=component_with_name(weak_self(), command[5])
				connector.connect(connectee)
			eval(command[3])()
		self.handler=TextCallback(handler)
		self.system=_skeleton.dlalBuildSystem(port, self.handler)
		assert(self.system)
		self.novel_components={}
		self.set('sampleRate', 44100)
		self.set('samplesPerEvaluation', 128)
		self.on_del=[]
		self.l=ReprMethod(self, 'load', start=True)

	def __del__(self):
		for i in self.on_del: i()
		_skeleton.dlalDemolishSystem(self.system)
		global _systems
		_systems-=1
		if _systems==0: _skeleton.dlalDyadShutdown()

	def add(self, *args, **kwargs):
		slot=kwargs.get('slot', 0)
		result=''
		for arg in args:
			for c in arg.get_components_to_add():
				result+=report(_skeleton.dlalAdd(self.system, c.component, slot))
				c.weak_system=weakref.ref(self)
			if len(result): result+='\n'
		return result

	def set(self, name, value):
		name=name.encode('utf-8')
		value=str(value).encode('utf-8')
		report(_skeleton.dlalSetVariable(self.system, name, value))

	def serialize(self):
		return report(_skeleton.dlalSerialize(self.system))

	def deserialize(self, serialized):
		state=json.loads(serialized)
		#variables
		for name, value in state['variables'].items():
			if name!='system.load':
				self.set(name, value)
		#components
		components={}
		for name, serialized in state['components'].items():
			component=component_builder(state['component_types'][name])(name=name)
			component.deserialize(serialized)
			components[name]=component
		for index, slot in enumerate(state['component_order']):
			for component in slot:
				component=components[component]
				self.register_novel_component(component)
				self.add(component, slot=index)
		#connections
		for input, output in state['connections']: components[input].connect(components[output])
		#extra
		state['map']=components
		return state

	def save(self, file_name='system.state.txt', extra={}):
		root=json.loads(self.serialize())
		root.update(extra)
		serialized=json.dumps(root, indent=2, sort_keys=True)
		with open(file_name, 'w') as file: file.write(serialized)
		self._report('save '+os.path.abspath(file_name))

	def load(self, file_name='system.state.txt', start=False):
		potential_expansion=os.path.join('..', '..', 'states', file_name+'.txt')
		if os.path.exists(potential_expansion): file_name=potential_expansion
		self.set('system.load', os.path.abspath(file_name))
		with open(file_name) as file: result=self.deserialize(file.read())
		if start: self.start()
		return result

	def start(self):
		if not hasattr(self, 'audio'): raise Exception('no audio component')
		atexit.register(lambda: self.audio.finish())
		return self.audio.start()

	def register_novel_component(self, component):
		name=component.to_str()
		self.novel_components[name]=component
		if not hasattr(self, name): setattr(self, name, component)

	def _report(self, report): _skeleton.dlalReport(self.system, report)

class Component:
	_libraries={}

	@staticmethod
	def from_dict(d, component_map):
		return component_map[d['component']]

	def to_dict(self): return {'component': self.to_str()}

	def set_components_to_add(self, components):
		self.components_to_add=[weakref.ref(i) for i in components]

	def get_components_to_add(self):
		return [i() for i in self.components_to_add]

	def __init__(self, component_type, **kwargs):
		self.component=None
		if component_type not in Component._libraries:
			Component._libraries[component_type]=obvious.load_lib(camel_case(component_type))
			Component._libraries[component_type].dlalBuildComponent.restype=ctypes.c_void_p
			Component._libraries[component_type].dlalBuildComponent.argtypes=[ctypes.c_char_p]
		self.library=Component._libraries[component_type]
		if 'component' in kwargs:
			self.component=kwargs['component']
		else:
			self.component=Component._libraries[component_type].dlalBuildComponent(
				kwargs.get('name', _namer.name(component_type))
			)
		self.weak=kwargs.get('weak', False)
		self.set_components_to_add([self])
		commands=[i.split()[0] for i in self.command('help').split('\n')[1:] if len(i)]
		weak_self=weakref.ref(self)
		def captain(command):
			return lambda *args: weak_self().command(command+' '+' '.join([str(i) for i in args]))
		for command in commands:
			if command not in dir(self): setattr(self, command, captain(command))

	def __del__(self):
		if self.component!=None and not self.weak:
			_skeleton.dlalDemolishComponent(self.component)

	def transfer_component(self):
		result=self.component
		self.component=None
		return result

	def command(self, command):
		command=command.encode('utf-8')
		return report(_skeleton.dlalCommand(self.component, command))

	def connect(self, output):
		return report(_skeleton.dlalConnect(self.output(), output.component))

	def output(self): return self.component

	def system(self): return _skeleton.dlalSystem(self.component)

	def rename(self, name): _skeleton.dlalRename(self.system(), self.component, name)

	def phase(self): return int(self.periodic_get().split()[1])

	def period(self): return int(self.periodic_get().split()[0])

class Pipe(Component):
	def __init__(self, *args):
		if not len(args): return
		self.component=args[0].component
		self.set_components_to_add([x for arg in args for x in arg.get_components_to_add()])

	def __del__(self): pass

	def __getitem__(self, i): return self.get_components_to_add()[i]

	def output(self): return self.get_components_to_add()[-1].component

def component_to_dict(self, members):
	result={i: getattr(self, i) for i in members}
	result={k: {'class': v.__class__.__name__, 'dict': v.to_dict()} for k, v in result.items()}
	return result

def component_try_import(component_type):
	try: exec('from .{} import {} as result'.format(
		component_type, camel_case(component_type)
	))
	except ImportError: return None
	return result

def component_builder(component_type):
	cls=component_try_import(component_type)
	if cls: return cls
	return lambda **kwargs: Component(component_type, **kwargs)

def component_from_dict(self, members, d, component_map):
	for member in members:
		class_name=d[member]['class']
		cls=component_try_import(snake_case(class_name))
		if not cls: cls=eval(class_name)
		setattr(self, member, cls.from_dict(d[member]['dict'], component_map))

def component_with_name(system, name):
	if isinstance(system, System): system=system.system
	component=_skeleton.dlalComponentWithName(system, name)
	component_type=report(_skeleton.dlalCommand(component, 'type'))
	return Component(component_type, component=component, weak=True)

def test(): _skeleton.dlalTest()

def regularize_component_constructors(globals):
	component_types=sorted(os.listdir(os.path.join(root, 'components')))
	for i in component_types:
		if not component_try_import(i):
			globals[i.capitalize()]=functools.partial(Component, i)
