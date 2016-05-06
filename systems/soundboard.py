import dlal

soundboard=dlal.Buffer()
system=dlal.SimpleSystem([soundboard])
soundboard.load_sounds()
go, ports=system.standard_system_functionality()
