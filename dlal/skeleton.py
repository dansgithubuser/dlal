import ctypes, platform

def upperfirst(s): return s[0].upper()+s[1:]

def load(name):
	if platform.system()!='Windows': name='lib'+upperfirst(name)+'.so'
	return ctypes.CDLL(name)

skeleton=load('skeleton')
skeleton.dlalDemolishComponent.argtypes=[ctypes.c_void_p]
skeleton.dlalBuildSystem.restype=ctypes.c_void_p
skeleton.dlalDemolishSystem.argtypes=[ctypes.c_void_p]
skeleton.dlalCommandComponent.restype=ctypes.c_char_p
skeleton.dlalCommandComponent.argtypes=[ctypes.c_void_p, ctypes.c_char_p]
skeleton.dlalConnectInput.restype=ctypes.c_char_p
skeleton.dlalConnectInput.argtypes=[ctypes.c_void_p, ctypes.c_void_p]
skeleton.dlalConnectOutput.restype=ctypes.c_char_p
skeleton.dlalConnectOutput.argtypes=[ctypes.c_void_p, ctypes.c_void_p]
skeleton.dlalAddComponent.restype=ctypes.c_char_p
skeleton.dlalAddComponent.argtypes=[ctypes.c_void_p, ctypes.c_void_p]

class System:
	def __init__(self): self.system=skeleton.dlalBuildSystem()
	def __del__(self): skeleton.dlalDemolishSystem(self.system)

component_libraries={}

class Component:
	def __init__(self, component):
		if component not in component_libraries:
			component_libraries[component]=load(component)
			component_libraries[component].dlalBuildComponent.restype=ctypes.c_void_p
		self.component=component_libraries[component].dlalBuildComponent()

	def __del__(self): skeleton.dlalDemolishComponent(self.component)

	def __getattr__(self, name):
		return lambda *args: self.command(name+' '+' '.join([str(arg) for arg in args]))

	def command(self, text):
		text=str.encode(text, 'utf-8')
		return self._report(
			skeleton.dlalCommandComponent(self.component, text)
		)

	def add(self, system):
		return self._report(
			skeleton.dlalAddComponent(system.system, self.component)
		)

	def connect_input(self, input):
		return self._report(
			skeleton.dlalConnectInput(self.component, input.component)
		)

	def connect_output(self, output):
		return self._report(
			skeleton.dlalConnectOutput(self.component, output.component)
		)

	def _report(self, text):
		if text.startswith(b'error'): raise RuntimeError(text)
		return text.decode('utf-8')
