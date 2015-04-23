#include "switch.hpp"

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Switch; }

namespace dlal{

Switch::Switch(): _current(nullptr) {
	registerCommand("set", "<input index>", [&](std::stringstream& ss){
		unsigned i;
		ss>>i;
		if(i>=_inputs.size()) return "error: index out of range";
		_current=_inputs[i];
		return "";
	});
}

std::string Switch::addInput(Component* input){
	_inputs.push_back(input);
	_current=input;
	return "";
}

std::string Switch::readyToEvaluate(){
	if(!_current) return "error: no inputs";
	return "";
}

float* Switch::readAudio(){ return _current.load()->readAudio(); }
MidiMessages* Switch::readMidi(){ return _current.load()->readMidi(); }
std::string* Switch::readText(){ return _current.load()->readText(); }

}//namespace dlal
