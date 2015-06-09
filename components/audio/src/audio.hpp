#ifndef DLAL_AUDIO_INCLUDED
#define DLAL_AUDIO_INCLUDED

#include <skeleton.hpp>

#include <portaudio.h>

namespace dlal{

class Audio: public Component{
	public:
		Audio();
		~Audio();
		std::string addInput(Component*);
		std::string addOutput(Component*);
		std::string readyToEvaluate();
		void evaluate(unsigned samples);
		float* readAudio();
		unsigned _underflows;
		float* _output;
		Component* _micReceiver;
	private:
		static const PaSampleFormat PA_SAMPLE_FORMAT=paFloat32;
		std::string start();
		std::string finish();
		unsigned _sampleRate, _log2SamplesPerCallback;
		PaStream* _paStream;
		std::vector<Component*> _inputs;
		bool _started;
		#ifdef TEST_AUDIO
			bool _test;
			float _testPhase;
		#endif
};

}//namespace dlal

#endif//#ifndef DLAL_AUDIO_INCLUDED
