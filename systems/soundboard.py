import dlal

soundboard=dlal.Buffer()
system=dlal.SimpleSystem([soundboard])
soundboard.render_sonic_drums()
soundboard.load_sounds()
go, ports=system.standard_system_functionality()
