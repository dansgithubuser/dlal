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

s=skeleton.dlalBuildSystem()
a=audio.dlalBuildComponent()
f=fm.dlalBuildComponent()
m=midi.dlalBuildComponent()
print skeleton.dlalAddComponent(s, m, 'midi')
print skeleton.dlalAddComponent(s, f, 'fm')
print skeleton.dlalAddComponent(s, a, 'audio')
print skeleton.dlalCommandComponent(s, 'audio', 'set 22050 6')
print skeleton.dlalConnectComponents(s, 'fm', 'audio')
print skeleton.dlalConnectComponents(s, 'midi', 'fm')
print skeleton.dlalCommandComponent(s, 'midi', 'test 90 3c 7f')
print skeleton.dlalCommandComponent(s, 'audio', 'start')

raw_input()
