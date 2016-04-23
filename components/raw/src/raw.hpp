#ifndef DLAL_RAW_INCLUDED
#define DLAL_RAW_INCLUDED

#include <skeleton.hpp>

#include <fstream>

namespace dlal{

class Raw: public Component{
	public:
		Raw();
		std::string type() const { return "raw"; }
		void evaluate();
		float* audio(){ return _audio.data(); }
		bool hasAudio(){ return true; }
	private:
		unsigned _sampleRate, _log2SamplesPerCallback;
		std::vector<float> _audio;
		unsigned _duration, _sample, _maxSample;
		std::string _fileName;
		std::ofstream _file;
};

}//namespace dlal

#endif//#ifndef DLAL_RAW_INCLUDED
