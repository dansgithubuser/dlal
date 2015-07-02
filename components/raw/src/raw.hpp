#ifndef DLAL_RAW_INCLUDED
#define DLAL_RAW_INCLUDED

#include <skeleton.hpp>

namespace dlal{

class Raw: public SystemGetter{
	public:
		Raw();
		float* audio(){ return _audio.data(); }
		bool hasAudio(){ return true; }
	private:
		unsigned _sampleRate, _log2SamplesPerCallback;
		std::vector<float> _audio;
		unsigned _duration;
		std::string _fileName;
};

}//namespace dlal

#endif//#ifndef DLAL_RAW_INCLUDED
