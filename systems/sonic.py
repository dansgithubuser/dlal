import dlal

sonic = dlal.Sonic()
system = dlal.SimpleSystem([sonic])
go, ports = system.standard_system_functionality()
