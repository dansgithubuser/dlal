import dlal, os

sonic_controller=dlal.SonicController()
vst=dlal.Component('vst')
system=dlal.SimpleSystem([sonic_controller, vst])
vst_path=dlal.tunefish_path()
if 'DLAL_VST_PLUGIN_PATH' in os.environ:
	vst_path=os.environ['DLAL_VST_PLUGIN_PATH']
vst.load(vst_path)
go, ports=system.standard_system_functionality()
