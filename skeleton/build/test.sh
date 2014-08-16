p=`pwd`
cd ../../components/audio/build
mkdir lib
cd lib
cmake -D BUILD_SHARED_LIBS=ON ..
make
cd $p

cmake -D BUILD_SHARED_LIBS=ON .
make

cp ../../components/audio/build/lib/libAudio.so .

export LD_LIBRARY_PATH=`pwd`
python test.py
