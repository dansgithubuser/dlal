#ifndef DLAL_FM_INCLUDED
#define DLAL_FM_INCLUDED

#include <skeleton.hpp>

namespace dlal{

class Sonic: public Component{
	public:
		Sonic();
		std::string addInput(Component*);
		std::string addOutput(Component*);
		std::string readyToEvaluate();
		void evaluate(unsigned samples);
	private:
		static const unsigned NOTES=128;
		static const unsigned OSCILLATORS=4;
		struct Runner{
			enum Stage{ ATTACK, DECAY, SUSTAIN, RELEASE };
			void start();
			void phase();
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
		void processMidi(const MidiMessage&);
		Oscillator _oscillators[OSCILLATORS];
		float* _samples;
		Note _notes[NOTES];
		std::string _text;
		Component* _input;
		Component* _output;
		bool _ready;
};

}//namespace dlal

#endif
