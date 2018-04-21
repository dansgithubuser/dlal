import dlal

sonic_controller=dlal.SonicController()
lpf=dlal.Component('lpf')
system=dlal.SimpleSystem([sonic_controller, lpf])
sonic_controller.show_controls()
go, ports=system.standard_system_functionality()
