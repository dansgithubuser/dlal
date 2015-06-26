#ifndef DLAL_AUDIO_INCLUDED
#define DLAL_AUDIO_INCLUDED

#include <skeleton.hpp>

namespace dlal{

class Raw: public Component{
	public:
		Raw();
		std::string addInput(Component*);
		std::string readyToEvaluate();
		void evaluate(unsigned samples);
		float* readAudio();
	private:
		unsigned _sampleRate, _log2SamplesPerCallback;
		std::vector<Component*> _inputs;
		std::vector<float> _output;
		unsigned _duration;
		std::string _fileName;
};

}//namespace dlal

#endif//#ifndef DLAL_AUDIO_INCLUDED
