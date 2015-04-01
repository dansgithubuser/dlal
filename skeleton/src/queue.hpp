#ifndef DLAL_QUEUE_INCLUDED
#define DLAL_QUEUE_INCLUDED

#include <vector>
#include <atomic>

namespace dlal{

//lockless single reader, single writer queue
template <typename T> class Queue{
	public:
		Queue(unsigned log2Size): _v(1<<log2Size), _mask(1), _r(0), _w(0) {
			if(log2Size>0) for(unsigned i=0; i<log2Size-1; ++i) _mask|=_mask<<1;
		}

		bool lockless(){ return _r.is_lock_free(); }

		bool read(T& t, bool next){
			unsigned r=_r.load(std::memory_order_relaxed);
			if(r==_w.load(std::memory_order_consume)) return false;
			t=_v[r];
			if(next) _r.store(r+1&_mask, std::memory_order_release);
			return true;
		}

		bool write(const T& t){
			unsigned w=_w.load(std::memory_order_relaxed);
			unsigned r=_r.load(std::memory_order_consume);
			if((w+1&_mask)==r) return false;
			_v[w]=t;
			_w.store(w+1&_mask, std::memory_order_release);
			return true;
		}

	private:
		std::vector<T> _v;
		unsigned _mask;
		std::atomic<unsigned> _r, _w;
};

}//namespace dlal

#endif
