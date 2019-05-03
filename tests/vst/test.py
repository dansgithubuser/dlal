#vst

import dlal

vst=dlal.Component('vst')
dlal.SimpleSystem.log_2_samples_per_evaluation=6
system=dlal.SimpleSystem([vst], test=True)
vst.load(dlal.tunefish_path(), immediate=True)
#Travis and AppVeyor don't have screens or something...
#vst.show_test(100, os.path.join(file_path, 'expected.png'))
go, ports=system.standard_system_functionality()
