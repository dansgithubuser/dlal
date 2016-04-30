import ctypes, os, platform

root=os.path.join(os.path.split(os.path.realpath(__file__))[0], '..')

_port=9088
_systems=0

def set_port(port):
	assert(_systems==0)
	global _port
	_port=port

def load(name):
	def upperfirst(s): return s[0].upper()+s[1:]
	if platform.system()!='Windows': name='lib'+upperfirst(name)+'.so'
	return ctypes.CDLL(name)

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

_skeleton=load('skeleton')
_skeleton.dlalDemolishComponent.argtypes=[ctypes.c_void_p]
_skeleton.dlalDyadInit.argtypes=[ctypes.c_int]
_skeleton.dlalBuildSystem.restype=ctypes.c_void_p
_skeleton.dlalDemolishSystem.argtypes=[ctypes.c_void_p]
_skeleton.dlalSetVariable.argtypes=[ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
_skeleton.dlalCommand.restype=ctypes.c_void_p
_skeleton.dlalCommand.argtypes=[ctypes.c_void_p, ctypes.c_char_p]
_skeleton.dlalAdd.restype=ctypes.c_void_p
_skeleton.dlalAdd.argtypes=[ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]
_skeleton.dlalConnect.restype=ctypes.c_void_p
_skeleton.dlalConnect.argtypes=[ctypes.c_void_p, ctypes.c_void_p]
_skeleton.dlalFree.argtypes=[ctypes.c_void_p]

class System:
	def __init__(self, port=9088):
		global _systems
		if _systems==0: _skeleton.dlalDyadInit(_port)
		_systems+=1
		self.system=_skeleton.dlalBuildSystem(9088)
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
		name=str.encode(name, 'utf-8')
		value=str.encode(value, 'utf-8')
		_skeleton.dlalSetVariable(self.system, name, value)

class Component:
	_libraries={}

	def __init__(self, component):
		self.recognized_commands=[]#prevents infinite recurse in __getattr__ if something fails
		if component not in Component._libraries:
			Component._libraries[component]=load(component)
			Component._libraries[component].dlalBuildComponent.restype=ctypes.c_void_p
		self.library=Component._libraries[component]
		self.component=Component._libraries[component].dlalBuildComponent()
		self.components_to_add=[self]
		self.recognized_commands=[i.split()[0] for i in self.command('help').split('\n')[1:] if len(i)]

	def __del__(self): _skeleton.dlalDemolishComponent(self.component)

	def __getattr__(self, name):
		if name in self.recognized_commands:
			return lambda *args: self.command(
				name+' '+' '.join([str(arg) for arg in args])
			)
		raise AttributeError

	def command(self, command):
		command=str.encode(command, 'utf-8')
		return report(_skeleton.dlalCommand(self.component, command))

	def connect(self, output):
		return report(_skeleton.dlalConnect(self.output(), output.component))

	def output(self): return self.component

class Pipe(Component):
	def __init__(self, *args):
		self.component=args[0].component
		self.components_to_add=[x for arg in args for x in arg.components_to_add]

	def __del__(self): pass

	def __getitem__(self, i): return self.components_to_add[i]

	def output(self): return self.components_to_add[-1].component
