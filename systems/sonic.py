import dlal

sonic=dlal.Sonic()
lpf=dlal.Component('lpf')
system=dlal.SimpleSystem([sonic, lpf])
sonic.show_controls()
go, ports=system.standard_system_functionality()
