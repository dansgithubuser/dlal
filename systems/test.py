import glob, subprocess, os, sys

#setup
tests=glob.glob('../../tests/*')
overall=0
print('RUNNING TESTS')
#loop over tests
for test in tests:
	#run test
	r=subprocess.call(['python', os.path.join(test, 'test.py')])
	#read result and expected
	def read(file_name):
		with open(file_name) as file: contents=file.read()
		return [float(x) for x in contents.split()]
	try:
		raw=read('raw.txt')
	except:
		r=1
	expected=read(os.path.join(test, 'expected.txt'))
	#compare result to expected
	if len(raw)!=len(expected): r=1
	else:
		error=0
		for i in range(len(raw)): error+=abs(raw[i]-expected[i])
		if error>0.001: r=1
	#report
	overall|=r
	print('-' if r else '+', os.path.split(test)[1])
#finish
if overall:
	print('TESTS HAVE FAILED!')
	sys.exit(-1)
print('ALL TESTS SUCCEEDED')
