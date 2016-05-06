import dlal

fm=dlal.Fm()
lpf=dlal.Component('lpf')
system=dlal.SimpleSystem([fm, lpf])
fm.show_controls()
go, ports=system.standard_system_functionality()
