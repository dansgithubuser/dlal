import dlal
import os

filea = dlal.Filea()
system = dlal.SimpleSystem([filea])
p = os.path.join('..', '..', 'components', 'filea', 'ambient')
filea.open_read(os.path.join(p, 'cave.ogg'))
filea.loop_crossfade(4)
go, ports = system.standard_system_functionality()
