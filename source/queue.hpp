#ifndef DLAL_QUEUE_INCLUDED
#define DLAL_QUEUE_INCLUDED

#include <vector>
#include <atomic>
#include <mutex>

namespace dlal{

//queue for single lockless reader and multiple lockfull writers
template <typename T> class Queue{
	public:
		Queue(unsigned log2Size): _v(1<<log2Size), _mask(0), _r(0), _w(0) {
			if(log2Size==0) return;
			_mask=1;
			for(unsigned i=0; i<log2Size-1; ++i) _mask|=_mask<<1;
		}

		bool lockless(){ return _r.is_lock_free(); }

		const T* getRead(){
			unsigned r=_r.load(std::memory_order_relaxed);
			if(r==_w.load(std::memory_order_consume)) return NULL;
			return &_v[r];
		}

		void nextRead(){
			unsigned r=_r.load(std::memory_order_relaxed);
			_r.store(r+1&_mask, std::memory_order_release);
		}

		bool write(const T& t){
			std::lock_guard<std::mutex> _lock(_mutex);
			unsigned w=_w.load(std::memory_order_consume);
			unsigned r=_r.load(std::memory_order_consume);
			if((w+1&_mask)==r) return false;
			_v[w]=t;
			_w.store(w+1&_mask, std::memory_order_release);
			return true;
		}

		void setAll(const T& t){
			for(unsigned i=0; i<_v.size(); ++i) _v[i]=t;
		}

	private:
		std::vector<T> _v;
		unsigned _mask;
		std::atomic<unsigned> _r, _w;
		std::mutex _mutex;
};

}//namespace dlal

#endif
