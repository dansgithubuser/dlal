#soundfont

import dlal

soundfont=dlal.Component('soundfont')
system=dlal.SimpleSystem([soundfont], test=True)
go, ports=system.standard_system_functionality()
