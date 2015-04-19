#include "multiplier.hpp"

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Multiplier; }

namespace dlal{

Multiplier::Multiplier(): _output(nullptr), _multiplier(1.0f) {
	registerCommand("set", "multiplier", [&](std::stringstream& ss){
		ss>>_multiplier;
		_text="";
	});
}

bool Multiplier::ready(){
	if(!_output){ _text="error: output not set"; return false; }
	_text="";
	return true;
}

void Multiplier::addOutput(Component* output){
	if(!output->readAudio()){ _text="error: output must have audio"; return; }
	_text="";
	_output=output;
}

void Multiplier::evaluate(unsigned samples){
	for(unsigned i=0; i<samples; ++i) _output->readAudio()[i]*=_multiplier;
}

std::string* Multiplier::readText(){ return &_text; }

}//namespace dlal
