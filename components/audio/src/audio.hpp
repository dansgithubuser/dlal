#ifndef DLAL_AUDIO_INCLUDED
#define DLAL_AUDIO_INCLUDED

#include <skeleton.hpp>

#include <portaudio.h>

#include <sstream>

namespace dlal{

class Audio: public Component{
	public:
		Audio();
		bool ready();
		void addInput(Component*);
		void evaluate(unsigned samples);
		float* readAudio();
		std::string* readText();
		void clearText();
		void sendText(const std::string&);
		std::string commands();
		unsigned _sampleRate, _underflows;
		float* _output;
	private:
		static const PaSampleFormat PA_SAMPLE_FORMAT=paFloat32;
		void start();
		void finish();
		void process(const std::string& text);
		unsigned _log2SamplesPerCallback;
		PaStream* _paStream;
		std::string _text;
		std::vector<Component*> _inputs;
		bool _started;
		#ifdef TEST_AUDIO
			bool _test;
			float _testPhase;
		#endif
};

}//namespace dlal

#endif//#ifndef DLAL_AUDIO_INCLUDED
