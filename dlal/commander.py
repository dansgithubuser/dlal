from .skeleton import *

class Commander(Component):
	def __init__(self):
		Component.__init__(self, 'commander')
		self.callback_type=ctypes.CFUNCTYPE(None, ctypes.c_char_p)
		self.library.dlalCommanderConnect.restype=ctypes.c_char_p
		self.library.dlalCommanderConnect.argtypes=[ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]
		self.library.dlalCommanderDisconnect.restype=ctypes.c_char_p
		self.library.dlalCommanderDisconnect.argtypes=[ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]
		self.library.dlalCommanderAdd.restype=ctypes.c_char_p
		self.library.dlalCommanderAdd.argtypes=[ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint]
		self.library.dlalCommanderSetCallback.restype=ctypes.c_char_p
		self.library.dlalCommanderSetCallback.argtypes=[ctypes.c_void_p, self.callback_type]
		self.set_callback(report)

	def queue_command(self, i, *args, **kwargs):
		edges_to_wait=kwargs.get('edges_to_wait', 0)
		return self.queue(i, edges_to_wait, *args)

	def queue_add(self, *args, **kwargs):
		slot=kwargs.get('slot', 0)
		edges_to_wait=kwargs.get('edges_to_wait', 0)
		result=''
		for arg in args:
			for c in arg.components_to_add:
				result+=report(self.library.dlalCommanderAdd(
					self.component, c.component, slot, edges_to_wait
				))
			if len(result): result+='\n';
		return result

	def queue_connect(self, *args, **kwargs):
		edges_to_wait=kwargs.get('edges_to_wait', 0)
		enable=kwargs.get('enable', True)
		if len(args)<=1: return
		result=''
		if enable:
			f=self.library.dlalCommanderConnect
		else:
			f=self.library.dlalCommanderDisconnect
		for i in range(len(args)-1):
			result+=report(f(
				self.component, args[i].component, args[i+1].component, edges_to_wait
			))
			if len(result): result+='\n'
		return result

	def set_callback(self, callback):
		self.callback=self.callback_type(callback)
		return report(
			self.library.dlalCommanderSetCallback(self.component, self.callback)
		)
