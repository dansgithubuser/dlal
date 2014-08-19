#ifndef DLAL_QUEUE_INCLUDED
#define DLAL_QUEUE_INCLUDED

#include <vector>
#include <atomic>

namespace dlal{

template <typename T> class Queue{
	public:
		Queue(unsigned size): _r(0), _w(0), _v(size) {}

		const T* read(){
			if(_r==_w) return NULL;
			return &_v[_r];
		}

		void nextRead(){
			_r=(_r+1)%_v.size();
		}

		T* write(){
			return &_v[_w];
		}

		bool nextWrite(){
			if(_w+1==_r) return false;
			_w=(_w+1)%_v.size();
			return true;
		}

	private:
		std::vector<T> _v;
		std::atomic<unsigned> _r, _w;
};

}//namespace dlal

#endif
