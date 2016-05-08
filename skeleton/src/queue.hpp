#ifndef DLAL_QUEUE_INCLUDED
#define DLAL_QUEUE_INCLUDED

#include <vector>
#include <atomic>

namespace dlal{

//lockless single reader, single writer queue
template <typename T> class Queue{
	public:
		Queue(unsigned log2Size): _r(0), _w(0) { resize(log2Size); }

		void resize(unsigned log2Size){
			_v.resize(1<<log2Size);
			_mask=1;
			if(log2Size>0) for(unsigned i=0; i<log2Size-1; ++i) _mask|=_mask<<1;
		}

		bool lockless(){ return _r.is_lock_free(); }

		bool read(T& t, bool next){ return read(&t, 1, next); }

		bool read(T* t, unsigned size, bool next){
			unsigned r=_r.load(std::memory_order_relaxed);
			unsigned w=_w.load(std::memory_order_consume);
			unsigned x=w>=r?w:w+_v.size();
			if(x<r+size) return false;
			if(t) for(unsigned i=0; i<size; ++i) t[i]=_v[(r+i)&_mask];
			if(next) _r.store((r+size)&_mask, std::memory_order_release);
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
