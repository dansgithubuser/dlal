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
		float* readAudio();
		MidiMessages* readMidi();
		std::string* readText();
	private:
		std::atomic<Component*> _current;
		std::vector<Component*> _inputs;
		std::vector<float> _emptyAudio;
		MidiMessages _emptyMidi;
		std::string _emptyText;
};

}//namespace dlal

#endif
