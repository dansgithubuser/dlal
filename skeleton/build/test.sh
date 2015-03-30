p=`pwd`
cd ../../components/audio/build
mkdir lib
cd lib
cmake -D BUILD_SHARED_LIBS=ON ..
make
cp *.so ../../../../skeleton/build/
cd $p

p=`pwd`
cd ../../components/fm/build
mkdir lib
cd lib
cmake -D BUILD_SHARED_LIBS=ON ..
make
cp *.so ../../../../skeleton/build/
cd $p

cmake -D BUILD_SHARED_LIBS=ON .
make

export LD_LIBRARY_PATH=`pwd`
python test.py
