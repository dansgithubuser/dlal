#ifndef DLAL_QUEUE_INCLUDED
#define DLAL_QUEUE_INCLUDED

#include <algorithm>
#include <atomic>
#include <vector>

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

		bool read(T& t, bool next){
			unsigned r=_r.load(std::memory_order_relaxed);
			unsigned w=_w.load(std::memory_order_consume);
			if(r==w) return false;
			t=_v[r];
			if(next) _r.store((r+1)&_mask, std::memory_order_release);
			return true;
		}

		bool read(T* t, unsigned size, bool next){
			unsigned r=_r.load(std::memory_order_relaxed);
			unsigned w=_w.load(std::memory_order_consume);
			unsigned x=w>=r?w:w+_v.size();
			if(x<r+size) return false;
			if(t){
				auto z=_v.size()-r;
				if(size<z){
					std::copy(_v.data()+r, _v.data()+r+size, t);
				}
				else{
					std::copy(_v.data()+r, _v.data()+_v.size(), t  );
					std::copy(_v.data()  , _v.data()+size-z   , t+z);
				}
			}
			if(next) _r.store((r+size)&_mask, std::memory_order_release);
			return true;
		}

		unsigned readSize(){
			return (_w-_r+_v.size())%_v.size();
		}

		bool write(const T& t){
			unsigned w=_w.load(std::memory_order_relaxed);
			unsigned r=_r.load(std::memory_order_consume);
			if((w+1&_mask)==r) return false;
			_v[w]=t;
			_w.store(w+1&_mask, std::memory_order_release);
			return true;
		}

		bool write(const T* t, unsigned size){
			unsigned w=_w.load(std::memory_order_relaxed);
			unsigned r=_r.load(std::memory_order_consume);
			if(r<=w){
				if(size>=_v.size()-(w-r)) return false;
			}
			else{
				if(w+size>=r) return false;
			}
			if(w+size>_v.size()){
				auto z=_v.size()-w;
				std::copy(t  , t+z   , _v.data()+w);
				std::copy(t+z, t+size, _v.data()  );
			}
			else{
				std::copy(t, t+size, _v.data()+w);
			}
			_w.store(w+size&_mask, std::memory_order_release);
			return true;
		}

	private:
		std::vector<T> _v;
		unsigned _mask;
		std::atomic<unsigned> _r, _w;
};

}//namespace dlal

#endif
