import ctypes, platform

def upperfirst(s): return s[0].upper()+s[1:]

def load(name):
	if platform.system()!='Windows': name='lib'+upperfirst(name)+'.so'
	return ctypes.CDLL(name)

skeleton=load('skeleton')
skeleton.dlalDemolishComponent.argtypes=[ctypes.c_void_p]
skeleton.dlalBuildSystem.restype=ctypes.c_void_p
skeleton.dlalDemolishSystem.argtypes=[ctypes.c_void_p]
skeleton.dlalCommand.restype=ctypes.c_char_p
skeleton.dlalCommand.argtypes=[ctypes.c_void_p, ctypes.c_char_p]
skeleton.dlalAdd.restype=ctypes.c_char_p
skeleton.dlalAdd.argtypes=[ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]
skeleton.dlalConnect.restype=ctypes.c_char_p
skeleton.dlalConnect.argtypes=[ctypes.c_void_p, ctypes.c_void_p]

def report(text):
	t=text.decode('utf-8')
	if t.startswith('error'): raise RuntimeError(t)
	return t

class System:
	def __init__(self): self.system=skeleton.dlalBuildSystem()
	def __del__(self): skeleton.dlalDemolishSystem(self.system)

	def add(self, *args, slot=0):
		result=''
		for arg in args:
			for c in arg.components_to_add:
				result+=report(skeleton.dlalAdd(self.system, c.component, slot))
			if len(result): result+='\n';
		return result

component_libraries={}

class Component:
	def __init__(self, component):
		if component not in component_libraries:
			component_libraries[component]=load(component)
			component_libraries[component].dlalBuildComponent.restype=ctypes.c_void_p
		self.library=component_libraries[component]
		self.component=component_libraries[component].dlalBuildComponent()
		self.components_to_add=[self]

	def __del__(self): skeleton.dlalDemolishComponent(self.component)

	def __getattr__(self, name):
		return lambda *args: self.command(
			name+' '+' '.join([str(arg) for arg in args])
		)

	def command(self, text):
		text=str.encode(text, 'utf-8')
		return report(skeleton.dlalCommand(self.component, text))

	def connect(self, output):
		return report(skeleton.dlalConnect(self.component, output.component))
