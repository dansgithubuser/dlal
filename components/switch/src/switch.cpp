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
	registerCommand("unset", "", [&](std::stringstream& ss){
		_current=nullptr;
		return "";
	});
	registerCommand("samples", "<samples per callback>", [&](std::stringstream& ss){
		unsigned samplesPerCallback;
		ss>>samplesPerCallback;
		_emptyAudio.resize(samplesPerCallback);
		return "";
	});
}

std::string Switch::addInput(Component* input){
	_inputs.push_back(input);
	return "";
}

float* Switch::readAudio(){
	Component* current=_current.load();
	if(current) return current->readAudio();
	else return _emptyAudio.data();
}

MidiMessages* Switch::readMidi(){
	Component* current=_current.load();
	if(current) return current->readMidi();
	else return &_emptyMidi;
}

std::string* Switch::readText(){
	Component* current=_current.load();
	if(current) return current->readText();
	else return &_emptyText;
}

}//namespace dlal
