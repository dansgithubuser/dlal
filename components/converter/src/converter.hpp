#ifndef DLAL_CONVERTER_INCLUDED
#define DLAL_CONVERTER_INCLUDED

#include <skeleton.hpp>

namespace dlal{

class Converter: public SamplesPerEvaluationGetter, public MultiOut{
	public:
		Converter();
		std::string type() const { return "converter"; }
		void* derived(){ return this; }
		void evaluate();
		float* audio(){ return _audio.data(); }
		bool hasAudio(){ return true; }
	private:
		std::vector<float> _audio;
		uint8_t _controller;
};

}//namespace dlal

#endif
