import ctypes

def upperfirst(s): return s[0].upper()+s[1:]

def load(name): return ctypes.CDLL('lib'+upperfirst(name)+'.so')

skeleton=load('skeleton')
skeleton.dlalQueryComponent.restype=ctypes.c_char_p
skeleton.dlalCommandComponent.restype=ctypes.c_char_p
skeleton.dlalCommandComponent.argtype=[ctypes.c_void_p, ctypes.c_char_p]
skeleton.dlalAddComponent.restype=ctypes.c_char_p
skeleton.dlalAddComponent.argtype=[ctypes.c_void_p, ctypes.c_void_p]
skeleton.dlalConnectComponents.restype=ctypes.c_char_p
skeleton.dlalConnectComponents.argtype=[ctypes.c_void_p, ctypes.c_void_p]

system=skeleton.dlalBuildSystem()

component_libraries={}

def report(text):
	if text.startswith('error'): raise RuntimeError(text)
	return text

class Component:
	def __init__(self, component):
		if component not in component_libraries:
			component_libraries[component]=load(component)
		self.component=component_libraries[component].dlalBuildComponent()

	def query(self):
		return report(skeleton.dlalQueryComponent(self.component))

	def command(self, text):
		return report(skeleton.dlalCommandComponent(self.component, text))

	def add(self):
		return report(skeleton.dlalAddComponent(system, self.component))

	def connect(self, output):
		return report(skeleton.dlalConnectComponents(self.component, output.component))
