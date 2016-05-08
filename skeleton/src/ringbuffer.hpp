#ifndef DLAL_RINGBUFFER_INCLUDED
#define DLAL_RINGBUFFER_INCLUDED

#include <cmath>
#include <vector>

namespace dlal{

template <typename T> class Ringbuffer{
	public:
		Ringbuffer(){}

		Ringbuffer(unsigned size, const T& t): _mask(1), _i(0) {
			unsigned log2Size=unsigned(std::log2(size)+1);
			_v.resize(1<<log2Size, t);
			if(log2Size>0) for(unsigned i=0; i<log2Size-1; ++i) _mask|=_mask<<1;
		}

		const T& read(unsigned i) const { return _v[(_i+i)&_mask]; }

		const T& readBack(unsigned i) const { return _v[(_i+_v.size()-1-i)&_mask]; }

		void write(const T& t){
			_v[_i]=t;
			++_i;
			_i&=_mask;
		}

		const T& max(unsigned w) const {
			T m=readBack(0); unsigned mi=0;
			for(unsigned i=1; i<w; ++i) if(readBack(i)>m){ m=readBack(i); mi=i; }
			return readBack(mi);
		}

	private:
		std::vector<T> _v;
		unsigned _mask, _i;
};

}//namespace dlal

#endif
