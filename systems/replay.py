import dlal
import os

filei = dlal.Component('filei')
file_path = 'file.txt'
if 'DLAL_REPLAY_FILE_PATH' in os.environ:
    file_path = os.environ['DLAL_REPLAY_FILE_PATH']
filei.name(file_path)
system = dlal.SimpleSystem([filei])
go, ports = system.standard_system_functionality()
