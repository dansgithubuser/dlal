import dlal
import os

filea=dlal.Component('filea')
p=os.path.join('..', '..', 'components', 'filea', 'ambient')
filea.open_read(os.path.join(p, 'cave.ogg'))
system=dlal.SimpleSystem([filea])
filea.loop_crossfade(4)
go, ports=system.standard_system_functionality()
