import ctypes, platform

def upperfirst(s): return s[0].upper()+s[1:]

def load(name):
	if platform.system()!='Windows': name='lib'+upperfirst(name)+'.so'
	return ctypes.CDLL(name)

skeleton=load('skeleton')
skeleton.dlalCommandComponent.restype=ctypes.c_char_p
skeleton.dlalCommandComponent.argtype=[ctypes.c_void_p, ctypes.c_char_p]
skeleton.dlalAddComponent.restype=ctypes.c_char_p
skeleton.dlalConnectInput.restype=ctypes.c_char_p
skeleton.dlalConnectOutput.restype=ctypes.c_char_p

class System:
	def __init__(self): self.system=skeleton.dlalBuildSystem()
	def __del__(self): skeleton.dlalDemolishSystem(self.system)

component_libraries={}

class Component:
	def __init__(self, component):
		if component not in component_libraries:
			component_libraries[component]=load(component)
		self.component=component_libraries[component].dlalBuildComponent()

	def __del__(self): skeleton.dlalDemolishComponent(self.component)

	def command(self, text):
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
		if text.startswith('error'): raise RuntimeError(text)
		return text
