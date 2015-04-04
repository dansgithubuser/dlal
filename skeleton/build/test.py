import ctypes

skeleton=ctypes.CDLL('libSkeleton.so')
skeleton.dlalAddComponent.restype=ctypes.c_char_p
skeleton.dlalAddComponent.argtype=[ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p]
skeleton.dlalConnectComponents.restype=ctypes.c_char_p
skeleton.dlalAddComponent.argtype=[ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
skeleton.dlalCommandComponent.restype=ctypes.c_char_p
skeleton.dlalAddComponent.argtype=[ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
audio=ctypes.CDLL('libAudio.so')
fm=ctypes.CDLL('libFm.so')
midi=ctypes.CDLL('libMidi.so')
sfml=ctypes.CDLL('libSfml.so')

s=skeleton.dlalBuildSystem()
cAudio=audio.dlalBuildComponent()
cFm1=fm.dlalBuildComponent()
cFm2=fm.dlalBuildComponent()
cMidi=midi.dlalBuildComponent()
cSfml=sfml.dlalBuildComponent()
print skeleton.dlalAddComponent(s, cSfml, 'sfml')
print skeleton.dlalAddComponent(s, cMidi, 'midi')
print skeleton.dlalAddComponent(s, cFm1, 'fm1')
print skeleton.dlalAddComponent(s, cFm2, 'fm2')
print skeleton.dlalAddComponent(s, cAudio, 'audio')
print skeleton.dlalCommandComponent(s, 'audio', 'set 22050 6')
print skeleton.dlalConnectComponents(s, 'fm1', 'audio')
print skeleton.dlalConnectComponents(s, 'fm2', 'audio')
print skeleton.dlalConnectComponents(s, 'midi', 'fm1')
print skeleton.dlalConnectComponents(s, 'sfml', 'fm2')
print skeleton.dlalCommandComponent(s, 'audio', 'start')

raw_input()
