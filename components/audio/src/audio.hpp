#ifndef DLAL_AUDIO_INCLUDED
#define DLAL_AUDIO_INCLUDED

#include <queue.hpp>
#include <skeleton.hpp>

#include <RtAudio.h>

namespace dlal{

class Audio: public MultiOut{
	public:
		Audio();
		~Audio(){ if(_started) finish(); }
		std::string type() const override { return "audio"; }
		void evaluate() override ;
		float* audio() override { return _output; }
		bool hasAudio() override { return true; }
		float* _input;
		float* _output;
		Queue<float> _queue;
	private:
		std::string start(int input=-1, int ouput=-1);
		std::string finish();
		unsigned _sampleRate, _log2SamplesPerEvaluation;
		RtAudio _rtAudio;
		bool _started;
		unsigned _underflows;
		#ifdef DLAL_AUDIO_TEST
			bool _test;
			float _testPhase;
		#endif
};

}//namespace dlal

#endif//#ifndef DLAL_AUDIO_INCLUDED
