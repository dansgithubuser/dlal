import glob, subprocess, os, sys

#setup
pattern='*'
if len(sys.argv)>1: pattern=sys.argv[1]
tests=glob.glob('../../tests/'+pattern)
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
		for i in range(len(raw)):
			if abs(raw[i]-expected[i])>0.00001:
				r=1
	#report
	overall|=r
	print('-' if r else '+', os.path.split(test)[1])
#finish
if overall:
	print('TESTS HAVE FAILED!')
	sys.exit(-1)
print('ALL TESTS SUCCEEDED')
