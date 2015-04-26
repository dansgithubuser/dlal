#helper
function test {
	if [ $? -ne 0 ]; then
		exit
	fi
}

#build
mkdir ../build/test
cd ../build/test
cmake -D BUILD_SHARED_LIBS=ON ..
test
make
test
export LD_LIBRARY_PATH=`pwd`
cd -

#run
export PYTHONPATH=`pwd`/..
python -i test.py 2> stderr.txt
