#ifndef DLAL_AUDIO_INCLUDED
#define DLAL_AUDIO_INCLUDED

#include <skeleton.hpp>

#include <portaudio.h>

#include <sstream>

namespace dlal{

class Audio: public Component{
	public:
		typedef float Sample;
		Audio();
		virtual void addInput(Component*);
		virtual void evaluate(unsigned samples);
		virtual float* readAudio();
		virtual std::string* readText();
		virtual void sendText(const std::string&);
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
		bool _test;
		float _testPhase;
};

}//namespace dlal

#endif//#ifndef DLAL_AUDIO_INCLUDED
