import dlal

soundboard=dlal.Buffer()
system=dlal.SimpleSystem([soundboard])
soundboard.render_fm_drums()
soundboard.load_sounds()
go, ports=system.standard_system_functionality()
