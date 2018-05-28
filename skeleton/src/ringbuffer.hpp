#ifndef DLAL_RINGBUFFER_INCLUDED
#define DLAL_RINGBUFFER_INCLUDED

#include <cmath>
#include <stdexcept>
#include <vector>

namespace dlal{

template <typename T> class Ringbuffer{
	public:
		Ringbuffer(){}

		Ringbuffer(unsigned size, const T& t): _mask(1), _i(0) {
			auto log2SizeF=std::log2(size);
			unsigned log2Size=unsigned(log2SizeF);
			if(log2SizeF-log2Size!=0) throw std::logic_error("size must be power of 2");
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

template <typename T> class ModRingbuffer{
	public:
		ModRingbuffer(){}

		ModRingbuffer(unsigned size, const T& t): _v(size, t), _i(0) {}

		const T& read(unsigned i) const { return _v[(_i+i)%_v.size()]; }

		const T& readBack(unsigned i) const { return _v[(_i+_v.size()-1-i)%_v.size()]; }

		void write(const T& t){
			_v[_i]=t;
			++_i;
			_i%=_v.size();
		}

		const T& max(unsigned w) const {
			T m=readBack(0); unsigned mi=0;
			for(unsigned i=1; i<w; ++i) if(readBack(i)>m){ m=readBack(i); mi=i; }
			return readBack(mi);
		}

	private:
		std::vector<T> _v;
		unsigned _i;
};

}//namespace dlal

#endif
