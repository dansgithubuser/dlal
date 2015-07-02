from .skeleton import *

class Commander(Component):
	def __init__(self):
		Component.__init__(self, 'commander')
		self.callback_type=ctypes.CFUNCTYPE(None, ctypes.c_char_p)
		self.library.dlalCommanderConnect.restype=ctypes.c_char_p
		self.library.dlalCommanderConnect.argtypes=[ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]
		self.library.dlalCommanderAdd.restype=ctypes.c_char_p
		self.library.dlalCommanderAdd.argtypes=[ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint]
		self.library.dlalCommanderSetCallback.restype=ctypes.c_char_p
		self.library.dlalCommanderSetCallback.argtypes=[ctypes.c_void_p, self.callback_type]

	def queue_add(self, component, slot=0, edgesToWait=0):
		return report(
			self.library.dlalCommanderAdd(self.component, component.component, slot, edgesToWait)
		)

	def queue_connect(self, input, output, edgesToWait=0):
		return report(
			self.library.dlalCommanderConnect(self.component, input.component, output.component, edgesToWait)
		)

	def set_callback(self, callback):
		self.callback=self.callback_type(callback)
		return report(
			self.library.dlalCommanderSetCallback(self.component, self.callback)
		)
