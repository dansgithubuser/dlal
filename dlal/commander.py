from .skeleton import *
from .skeleton import _skeleton

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
		self.novel_components=[]
		def queue_add(text):
			_, type=text.decode('utf-8').split()
			self.queue_add(type)
		self.register_command('queue_add', queue_add)
		def queue_connect(text):
			_, connector, connectee=text.decode('utf-8').split()
			self.queue_connect(connector, connectee)
		self.register_command('queue_connect', queue_connect)
		def queue_disconnect(text):
			_, connector, connectee=text.decode('utf-8').split()
			self.queue_connect(connector, connectee, enable=False)
		self.register_command('queue_disconnect', queue_disconnect)

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
		def add(component):
			return report(self.library.dlalCommanderAdd(self.component, component, slot, edges_to_wait))
		for arg in args:
			if type(arg) in [str, unicode]:
				component=Component(arg)
				self.novel_components.append(component)
				result+=add(component.component)
			else:
				for c in arg.components_to_add: result+=add(c.component)
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
		def componentify(arg, connectee):
			if type(arg) in [str, unicode]:
				return _skeleton.dlalComponentWithName(self.system(), arg)
			return arg.output() if connectee else arg.component
		for i in range(len(args)-1):
			result+=report(f(
				self.component,
				componentify(args[i  ], True ),
				componentify(args[i+1], False),
				edges_to_wait
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
