import ctypes
import json
import os
import platform
import subprocess
import sys

root=os.path.join(os.path.split(os.path.realpath(__file__))[0], '..')
sys.path.append(os.path.join(root, 'deps', 'obvious'))

import obvious

def invoke(invocation):
	subprocess.check_call(invocation, shell=True)

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

_skeleton=obvious.load_lib('Skeleton')
_skeleton.dlalDemolishComponent.argtypes=[ctypes.c_void_p]
_skeleton.dlalBuildSystem.restype=ctypes.c_void_p
_skeleton.dlalDemolishSystem.argtypes=[ctypes.c_void_p]
_skeleton.dlalSetVariable.restype=ctypes.c_void_p
_skeleton.dlalSetVariable.argtypes=[ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
_skeleton.dlalCommand.restype=ctypes.c_void_p
_skeleton.dlalCommand.argtypes=[ctypes.c_void_p, ctypes.c_char_p]
_skeleton.dlalAdd.restype=ctypes.c_void_p
_skeleton.dlalAdd.argtypes=[ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]
_skeleton.dlalConnect.restype=ctypes.c_void_p
_skeleton.dlalConnect.argtypes=[ctypes.c_void_p, ctypes.c_void_p]
_skeleton.dlalSystem.restype=ctypes.c_void_p
_skeleton.dlalSystem.argtypes=[ctypes.c_void_p]
_skeleton.dlalSerialize.restype=ctypes.c_void_p
_skeleton.dlalSerialize.argtypes=[ctypes.c_void_p]
_skeleton.dlalFree.argtypes=[ctypes.c_void_p]

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
		self.system=_skeleton.dlalBuildSystem(port)
		assert(self.system)

	def __del__(self):
		_skeleton.dlalDemolishSystem(self.system)
		global _systems
		_systems-=1
		if _systems==0: _skeleton.dlalDyadShutdown()

	def add(self, *args, **kwargs):
		slot=kwargs.get('slot', 0)
		result=''
		for arg in args:
			for c in arg.components_to_add:
				result+=report(_skeleton.dlalAdd(self.system, c.component, slot))
			if len(result): result+='\n';
		return result

	def set(self, name, value):
		name=name.encode('utf-8')
		value=value.encode('utf-8')
		report(_skeleton.dlalSetVariable(self.system, name, value))

	def serialize(self):
		return report(_skeleton.dlalSerialize(self.system))

	def deserialize(self, serialized):
		state=json.loads(serialized)
		#variables
		for name, value in state['variables'].items(): self.set(name, value)
		#components
		components={}
		for name, serialized in state['components'].items():
			component=Component(state['component_types'][name])
			component.deserialize(serialized)
			components[name]=component
		for slot in state['component_order']:
			for index, component in enumerate(slot):
				self.add(components[component], slot=index)
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

	def load(self, file_name='system.state.txt'):
		with open(file_name) as file: return self.deserialize(file.read())

class Component:
	_libraries={}

	@staticmethod
	def from_dict(d, component_map):
		return component_map[d['component']]

	def to_dict(self): return {'component': self.to_str()}

	def __init__(self, component_type, **kwargs):
		if component_type not in Component._libraries:
			Component._libraries[component_type]=obvious.load_lib(component_type.capitalize())
			Component._libraries[component_type].dlalBuildComponent.restype=ctypes.c_void_p
		self.library=Component._libraries[component_type]
		self.component=kwargs.get('component',
			Component._libraries[component_type].dlalBuildComponent()
		)
		self.components_to_add=[self]
		commands=[i.split()[0] for i in self.command('help').split('\n')[1:] if len(i)]
		def captain(command):
			return lambda *args: self.command(command+' '+' '.join([str(i) for i in args]))
		for command in commands:
			if command not in dir(self): setattr(self, command, captain(command))

	def __del__(self):
		if self.component!=None: _skeleton.dlalDemolishComponent(self.component)

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

class Pipe(Component):
	def __init__(self, *args):
		if not len(args): return
		self.component=args[0].component
		self.components_to_add=[x for arg in args for x in arg.components_to_add]

	def __del__(self): pass

	def __getitem__(self, i): return self.components_to_add[i]

	def output(self): return self.components_to_add[-1].component

def component_to_dict(self, members):
	result={i: getattr(self, i) for i in members}
	result={k: {'class': v.__class__.__name__, 'dict': v.to_dict()} for k, v in result.items()}
	return result

def component_from_dict(self, members, d, component_map):
	for member in members:
		try: exec('from {} import *').format(d[member]['class'].lower())
		except ImportError: pass
		cls=eval(d[member]['class'])
		setattr(self, member, cls.from_dict(d[member]['dict'], component_map))

def test(): _skeleton.dlalTest()
