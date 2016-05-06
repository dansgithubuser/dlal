import dlal, os

soundfont=dlal.Component('soundfont')
system=dlal.SimpleSystem([soundfont])
soundfont.load(os.path.join('..', '..', 'components', 'soundfont', 'deps', '32MbGMStereo.sf2'))
go, ports=system.standard_system_functionality()
