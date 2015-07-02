#ifndef DLAL_FM_INCLUDED
#define DLAL_FM_INCLUDED

#include <skeleton.hpp>

namespace dlal{

class Sonic:
	public MultiOut, public SamplesPerEvaluationGetter, public SampleRateGetter
{
	public:
		Sonic();
		void evaluate();
		void midi(const uint8_t* bytes, unsigned size);
		bool midiAccepted(){ return true; }
	private:
		static const unsigned NOTES=128;
		static const unsigned OSCILLATORS=4;
		struct Runner{
			Runner();
			void start();
			void phase();
			enum Stage{ ATTACK, DECAY, SUSTAIN, RELEASE };
			Stage _stage;
			float _phase, _step, _volume, _output;
		};
		struct Oscillator{
			Oscillator();
			bool update(Runner&) const;//returns true if the runner is done
			float _attack, _decay, _sustain, _release;
			float _frequencyMultiplier, _inputs[OSCILLATORS];
			float _output;
		};
		struct Note{
			Note();
			void set(unsigned i, unsigned sampleRate, const Oscillator* oscillators);
			void start(float volume, const Oscillator* oscillators);
			void stop();
			float update(//returns output
				unsigned,//index of runner
				const Oscillator* oscillators
			);
			Runner _runners[OSCILLATORS];
			float _volume;
			bool _done;
		};
		void update();
		Oscillator _oscillators[OSCILLATORS];
		Note _notes[NOTES];
};

}//namespace dlal

#endif
