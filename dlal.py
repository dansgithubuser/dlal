import ctypes, copy

def upperfirst(s): return s[0].upper()+s[1:]

def load(name): return ctypes.CDLL('lib'+upperfirst(name)+'.so')

skeleton=load('skeleton')
skeleton.dlalReadComponent.restype=ctypes.c_char_p
skeleton.dlalCommandComponent.restype=ctypes.c_char_p
skeleton.dlalCommandComponent.argtype=[ctypes.c_void_p, ctypes.c_char_p]
skeleton.dlalAddComponent.restype=ctypes.c_char_p
skeleton.dlalConnectComponents.restype=ctypes.c_char_p

system=skeleton.dlalBuildSystem()

component_libraries={}

class Component:
	def __init__(self, component):
		if component not in component_libraries:
			component_libraries[component]=load(component)
		self.component=component_libraries[component].dlalBuildComponent()
		self.report('')

	def command(self, text):
		return self.report(skeleton.dlalCommandComponent(self.component, text))

	def add(self):
		return self.report(skeleton.dlalAddComponent(system, self.component))

	def connect(self, output):
		return self.report(
			skeleton.dlalConnectComponents(self.component, output.component),
			output.component
		)

	def report(self, text, other=None):
		fText=copy.deepcopy(text)
		cText=copy.deepcopy(skeleton.dlalReadComponent(self.component))
		oText=''
		if other: oText=copy.deepcopy(skeleton.dlalReadComponent(other))
		text=''
		if fText: text+=fText+'\n'
		if cText: text+=cText+'\n'
		if oText: text+=oText+'\n'
		for i in [fText, cText, oText]:
			if i.startswith('error'):
				raise RuntimeError(text)
		return text
