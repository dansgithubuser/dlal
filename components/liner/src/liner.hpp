#ifndef DLAL_LINER_INCLUDED
#define DLAL_LINER_INCLUDED

#include <skeleton.hpp>

#include <vector>

namespace dlal{

class Liner: public Component{
	public:
		Liner();
		std::string readyToEvaluate();
		void evaluate(unsigned samples);
		MidiMessages* readMidi();
	private:
		struct TimedMidi{
			unsigned _sample;
			MidiMessages _midi;
		};
		std::vector<TimedMidi> _line;
		MidiMessages _midi;
		unsigned _sample, _index, _period;
};

}//namespace dlal

#endif
