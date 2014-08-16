import ctypes

skeleton=ctypes.CDLL('libSkeleton.so')
audio=ctypes.CDLL('libAudio.so')

s=skeleton.dlalBuildSystem()
a=audio.dlalBuildComponent()
print skeleton.dlalAddComponent(s, a, ctypes.c_char_p('audio'))
print skeleton.dlalCommandComponent(s, ctypes.c_char_p('audio'), ctypes.c_char_p('test'))
print skeleton.dlalCommandComponent(s, ctypes.c_char_p('audio'), ctypes.c_char_p('start 22050 6'))

raw_input()
