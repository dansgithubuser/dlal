#ifndef DLAL_CONVERTER_INCLUDED
#define DLAL_CONVERTER_INCLUDED

#include <skeleton.hpp>

namespace dlal{

class Converter: public SamplesPerEvaluationGetter, public MultiOut{
	public:
		Converter();
		std::string type() const override { return "converter"; }
		void* derived() override { return this; }
		void evaluate() override;
		float* audio() override { return _audio.data(); }
		bool hasAudio() override { return true; }
	private:
		std::vector<float> _audio;
		uint8_t _controller;
};

}//namespace dlal

#endif
