import dlal

soundboard=dlal.Buffer()
soundboard.render_sonic_drums()
system=dlal.SimpleSystem([soundboard])
soundboard.load_sounds()
go, ports=system.standard_system_functionality()
