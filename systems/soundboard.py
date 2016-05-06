import dlal

soundboard=dlal.Buffer()
soundboard.periodic_resize(64)
system=dlal.SimpleSystem([soundboard])
soundboard.load_sounds()
go, ports=system.standard_system_functionality()
