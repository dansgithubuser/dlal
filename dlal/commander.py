from .skeleton import *

class Commander(Component):
	def __init__(self):
		Component.__init__(self, 'commander')
		self.library.dlalCommanderConnectInput.restype=ctypes.c_char_p
		self.library.dlalCommanderConnectInput.argtypes=[ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]
		self.library.dlalCommanderConnectOutput.restype=ctypes.c_char_p
		self.library.dlalCommanderConnectOutput.argtypes=[ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]
		self.library.dlalCommanderAddComponent.restype=ctypes.c_char_p
		self.library.dlalCommanderAddComponent.argtypes=[ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]

	def queue_connect_input(self, component, input, periodEdgesToWait):
		return self._report(
			self.library.dlalCommanderConnectInput(self.component, component.component, input.component, periodEdgesToWait)
		)

	def queue_connect_output(self, component, output, periodEdgesToWait):
		return self._report(
			self.library.dlalCommanderConnectOutput(self.component, component.component, output.component, periodEdgesToWait)
		)

	def queue_add(self, component, periodEdgesToWait):
		return self._report(
			self.library.dlalCommanderAddComponent(self.component, component.component, periodEdgesToWait)
		)
