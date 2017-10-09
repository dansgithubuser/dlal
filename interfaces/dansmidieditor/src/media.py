import ctypes
sfml=ctypes.CDLL('../../../build/built/libSfml.so')
assert sfml.init(640, 480, "Dan's MIDI Editor")==0
sfml.poll_event.restype=ctypes.c_char_p

def poll_event(): return sfml.poll_event().decode()
def set_vertices_type(s): sfml.set_vertices_type(s)
def vertex(x, y, r, g, b, a): sfml.vertex(x, y, r, g, b, a)
def draw_vertices(): sfml.draw_vertices()
def width(): return sfml.width()
def height(): return sfml.height()
def display(): sfml.draw_vertices(); sfml.display()

def _xi_yi(**kwargs):
	if 'bounds' in kwargs:
		xi, yi, xf, yf=kwargs['bounds']
	if 'xi' in kwargs:
		xi=kwargs['xi']
		xf=kwargs['xf']
	if 'yi' in kwargs:
		yi=kwargs['yi']
		yf=kwargs['yf']
	if 'x' in kwargs:
		xi=kwargs['x']
		xf=xi+kwargs['w']
	if 'y' in kwargs:
		yi=kwargs['y']
		yf=yi+kwargs['h']
	if kwargs.get('right', False):
		d=xf-xi
		xi-=d
		xf-=d
	if kwargs.get('bottom', False):
		d=yf-yi
		yi-=d
		yf-=d
	if kwargs.get('middle_x', False):
		d=(xf-xi)/2
		xi-=d
		xf-=d
	if kwargs.get('middle_y', False):
		d=(yf-yi)/2
		yi-=d
		yf-=d
	return (xi, yi, xf, yf)

def _color(**kwargs):
	r=kwargs.get('r', 255)
	g=kwargs.get('g', 255)
	b=kwargs.get('b', 255)
	a=kwargs.get('a', 255)
	c=kwargs.get('color', ())
	if   len(c)==3: r, g, b   =c
	elif len(c)==4: r, g, b, a=c
	return (r, g, b, a)

def text(s, **kwargs):
	kwargs['xf']=0
	kwargs['w' ]=0
	xi, yi, xf, yf=_xi_yi(**kwargs)
	r, g, b, a=_color(**kwargs)
	sfml.text(xi, yi, yf-yi, s.encode(), r, g, b, a)

def fill(**kwargs):
	set_vertices_type('triangles')
	xi, yi, xf, yf=_xi_yi(**kwargs)
	r, g, b, a=_color(**kwargs)
	vertex(xi, yi, r, g, b, a)
	vertex(xf, yi, r, g, b, a)
	vertex(xi, yf, r, g, b, a)
	vertex(xi, yf, r, g, b, a)
	vertex(xf, yi, r, g, b, a)
	vertex(xf, yf, r, g, b, a)

def line(**kwargs):
	set_vertices_type('lines')
	xi, yi, xf, yf=_xi_yi(**kwargs)
	r, g, b, a=_color(**kwargs)
	vertex(xi, yi, r, g, b, a)
	vertex(xf, yf, r, g, b, a)

def clear(**kwargs):
	fill(x=0, y=0, w=width(), h=height(), color=_color(**kwargs))
	draw_vertices()
