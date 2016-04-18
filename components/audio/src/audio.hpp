#ifndef DLAL_AUDIO_INCLUDED
#define DLAL_AUDIO_INCLUDED

#include <skeleton.hpp>

#include <portaudio.h>

namespace dlal{

class Audio: public MultiOut{
	public:
		Audio();
		~Audio(){ if(_started) finish(); }
		std::string type() const { return "audio"; }
		void evaluate();
		float* audio(){ return _output; }
		bool hasAudio(){ return true; }
		float* _input;
		float* _output;
	private:
		static const PaSampleFormat PA_SAMPLE_FORMAT=paFloat32;
		std::string start();
		std::string finish();
		unsigned _sampleRate, _log2SamplesPerCallback;
		PaStream* _paStream;
		bool _started;
		unsigned _underflows;
		#ifdef DLAL_AUDIO_TEST
			bool _test;
			float _testPhase;
		#endif
};

}//namespace dlal

#endif//#ifndef DLAL_AUDIO_INCLUDED
