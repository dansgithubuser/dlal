from .skeleton import *

import os
import sys
import threading
import weakref

HOME=os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(HOME, '..', 'deps', 'simple-websocket-server'))

from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket

def network_web_socket(network):
	class NetworkWebSocket(WebSocket):
		def handleMessage(self): network().forward_data(self.data)
	return NetworkWebSocket

def worker(web_socketer):
	while not web_socketer.quit:
		web_socketer.server.serveonce()

class WebSocketer:
	def __init__(self, network, port):
		self.server=SimpleWebSocketServer('', port, network_web_socket(weakref.ref(network)))
		self.thread=threading.Thread(target=worker, args=(self,))
		self.thread.daemon=True
		self.quit=False
		self.thread.start()

	def finish(self):
		self.quit=True
		self.server.close()

class Network(Component):
	def __init__(self, **kwargs):
		Component.__init__(self, 'network', **kwargs)
		self.web_socketer=None

	def __del__(self):
		if self.web_socketer is not None: self.web_socketer.finish()
		Component.__del__(self)

	def open_web_socket(self):
		self.web_socketer=WebSocketer(self, int(self.port())+20000)

	def port(self, number=None):
		if number is None:
			return self.command('port')
		else:
			self.command('port {}'.format(number))
			self.open_web_socket()

	def deserialize(self, serialized):
		result=self.command('deserialize '+serialized)
		self.open_web_socket()
		return result
