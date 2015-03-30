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

s=skeleton.dlalBuildSystem()
a=audio.dlalBuildComponent()
f=fm.dlalBuildComponent()
print skeleton.dlalAddComponent(s, f, 'fm')
print skeleton.dlalAddComponent(s, a, 'audio')
print skeleton.dlalCommandComponent(s, 'audio', 'set 22050 6')
print skeleton.dlalConnectComponents(s, 'fm', 'audio')
print skeleton.dlalCommandComponent(s, 'fm', 'test')
print skeleton.dlalCommandComponent(s, 'audio', 'start')

raw_input()
