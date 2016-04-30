import os, shutil, sys

for path, folders, files in os.walk(os.path.join(sys.argv[1], sys.argv[2])):
	for file in files:
		if file in ['openal32.dll']:
			src=os.path.join(path, file)
			dst=os.path.join(sys.argv[1], file)
			print('{} ---> {}'.format(src, dst))
			shutil.copyfile(src, dst)
