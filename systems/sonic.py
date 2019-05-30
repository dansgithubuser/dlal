import dlal

sonic = dlal.Sonic()
system = dlal.SimpleSystem([sonic])
sonic.show_controls()
go, ports = system.standard_system_functionality()
