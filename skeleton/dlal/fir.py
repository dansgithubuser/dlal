from ._component import Component

import math

def flip_odd(i):
    if i % 2:
        return -1
    else:
        return +1

class Vec3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __neg__(self):
        return Vec3(
            -self.x,
            -self.y,
            -self.z,
        )

    def __add__(self, other):
        return Vec3(
            self.x + other.x,
            self.y + other.y,
            self.z + other.z,
        )

    def __sub__(self, other):
        return Vec3(
            self.x - other.x,
            self.y - other.y,
            self.z - other.z,
        )

    def __iadd__(self, other):
        self.x += other.x,
        self.y += other.y,
        self.z += other.z,
        return self

    def __mul__(self, other):
        return Vec3(
            other * self.x,
            other * self.y,
            other * self.z,
        )

    def __imul(self, other):
        self.x *= other
        self.y *= other
        self.z *= other
        return self

    def __truediv__(self, other):
        return self * (1/other)

    def mag2(self):
        return self.x ** 2 + self.y ** 2 + self.z ** 2

    def mag(self):
        return math.sqrt(self.mag2())

    def norm(self):
        return self / self.mag()

    def mul_components(self, other):
        return Vec3(
            self.x * other.x,
            self.y * other.y,
            self.z * other.z,
        )

    def dot(self, other):
        return (
            self.x * other.x
            + self.y * other.y
            + self.z * other.z
        )

class Box:
    def __init__(self, l, r, d, u, b, f):
        self.l = l
        self.r = r
        self.d = d
        self.u = u
        self.b = b
        self.f = f

class Room:
    def __init__(
        self,
        size=(7, 3, 5),
        *,
        p_ear=(-0.1, 0, -2),
        d_ear=(-1, 0, 0),
        ear_directionality=0.9,
        damp=(0.9, 0.9, 0.6, 0.8, 0.7, 0.7),
    ):
        '''
            `size` is the size of the room. Room is centered at origin.
            `p_ear` is the position of the ear.
            `d_ear` is the direction of the ear. Sources in this direction are loudest.
            `ear_directionality` is how much a source is dampened when coming from behind the ear.
            `damp` is how much each wall reflects sound. Left, right, down, up, back, front.
        '''
        self.size = Vec3(*size)
        self.p_ear = Vec3(*p_ear)
        self.d_ear = Vec3(*d_ear)
        self.ear_directionality = ear_directionality
        self.damp = Box(*damp)

    def flip_ear(self, head_size=0.2):
        self.d_ear *= -1
        self.p_ear += self.d_ear.norm() * head_size

    def ir(
        self,
        p_src,
        *,
        d_src=(0, 0, -1),
        src_directionality=0,
        gain=10,
        sample_rate=44100,
        order=32,
        speed_of_sound=343,
        threshold=1e-5,
    ):
        p_src = Vec3(*p_src)
        d_src = Vec3(*d_src)
        ir = [0]
        for i in range(-order, order+1):
            for j in range(-order, order+1):
                for k in range(-order, order+1):
                    ijk = Vec3(i, j, k)
                    m = Vec3(
                        (i % 2 * -2 + 1),
                        (j % 2 * -2 + 1),
                        (k % 2 * -2 + 1),
                    )
                    p_ear = self.size.mul_components(ijk) + self.p_ear.mul_components(m)
                    s = p_src - p_ear
                    s_mag = max(s.mag(), 1)
                    amp = gain / s_mag
                    amp *= self.damp.l ** (abs((i+0) // 2))
                    amp *= self.damp.r ** (abs((i+1) // 2))
                    amp *= self.damp.d ** (abs((j+0) // 2))
                    amp *= self.damp.u ** (abs((j+1) // 2))
                    amp *= self.damp.b ** (abs((k+0) // 2))
                    amp *= self.damp.f ** (abs((k+1) // 2))
                    d_ear = self.d_ear.mul_components(m)
                    amp *= self.ear_directionality * max(d_ear.dot(s.norm()), 0) + (1 - self.ear_directionality)
                    amp *= src_directionality * max(d_src.dot(-s.norm()), 0) + (1 - src_directionality)
                    if amp < threshold: continue
                    t = s_mag / speed_of_sound * sample_rate
                    a = int(t)
                    u = t - a
                    while a+1 >= len(ir): ir.append(0)
                    ir[a+0] += (1-u) * amp
                    ir[a+1] += (  u) * amp
        return ir

class Fir(Component):
    Room = Room

    def __init__(self, ir=None, **kwargs):
        Component.__init__(self, 'fir', **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            if ir != None: self.ir(ir)
