from .skeleton import *

class Commander(Component):
	@staticmethod
	def from_dict(d, component_map):
		return Commander(component=component_map[d['component']].transfer_component())

	def __init__(self, **kwargs):
		Component.__init__(self, 'commander', **kwargs)
		self.callback_type=ctypes.CFUNCTYPE(None, ctypes.c_char_p)
		self.library.dlalCommanderCommand.restype=ctypes.c_void_p
		self.library.dlalCommanderCommand.argtypes=[ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint]
		self.library.dlalCommanderAdd.restype=ctypes.c_void_p
		self.library.dlalCommanderAdd.argtypes=[ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint]
		self.library.dlalCommanderConnect.restype=ctypes.c_void_p
		self.library.dlalCommanderConnect.argtypes=[ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]
		self.library.dlalCommanderDisconnect.restype=ctypes.c_void_p
		self.library.dlalCommanderDisconnect.argtypes=[ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]
		self.library.dlalCommanderRegisterCommand.restype=ctypes.c_void_p
		self.library.dlalCommanderRegisterCommand.argtypes=[ctypes.c_void_p, ctypes.c_char_p, self.callback_type]
		self.commands=[]#to prevent python from garbage-collecting callbacks sent c-side

	def queue_command(self, component, *args, **kwargs):
		edges_to_wait=kwargs.get('edges_to_wait', 0)
		return report(self.library.dlalCommanderCommand(
			self.component,
			component.component,
			' '.join([str(arg) for arg in args]).encode('utf-8'),
			edges_to_wait
		))

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
				self.component, args[i].output(), args[i+1].component, edges_to_wait
			))
			if len(result): result+='\n'
		return result

	def register_command(self, name, command):
		command=self.callback_type(command)
		self.commands.append(command)
		return report(
			self.library.dlalCommanderRegisterCommand(
				self.component, name.encode('utf-8'), command
			)
		)
