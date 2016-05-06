#vst

import dlal

vst=dlal.Component('vst')
system=dlal.SimpleSystem([vst], test=True)
vst.load(dlal.tunefish_path())
#Travis and AppVeyor don't have screens or something...
#vst.show_test(100, os.path.join(file_path, 'expected.png'))
go, ports=system.standard_system_functionality()
