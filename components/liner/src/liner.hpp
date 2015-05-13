#ifndef DLAL_LINER_INCLUDED
#define DLAL_LINER_INCLUDED

#include <skeleton.hpp>

#include <vector>
#include <map>
#include <cstdint>

namespace dlal{

class Liner: public Component{
	public:
		Liner();
		std::string addInput(Component*);
		std::string readyToEvaluate();
		void evaluate(unsigned samples);
		MidiMessages* readMidi();
	private:
		std::map<uint64_t, MidiMessages> _line;
		MidiMessages _emptyMidi;
		MidiMessages* _midi;
		uint64_t _sample, _period;
		std::vector<Component*> _inputs;
};

}//namespace dlal

#endif
