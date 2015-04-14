#build
mkdir ../build/test
cd ../build/test
cmake -D BUILD_SHARED_LIBS=ON ..
make
export LD_LIBRARY_PATH=`pwd`
cd -

#run
export PYTHONPATH=`pwd`/..
python test.py
