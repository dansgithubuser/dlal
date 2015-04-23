#ifndef DLAL_SWITCH_INCLUDED
#define DLAL_SWITCH_INCLUDED

#include <skeleton.hpp>

#include <atomic>
#include <vector>

namespace dlal{

class Switch: public Component{
	public:
		Switch();
		std::string addInput(Component*);
		std::string readyToEvaluate();
		float* readAudio();
		MidiMessages* readMidi();
		std::string* readText();
	private:
		std::atomic<Component*> _current;
		std::vector<Component*> _inputs;
};

}//namespace dlal

#endif
