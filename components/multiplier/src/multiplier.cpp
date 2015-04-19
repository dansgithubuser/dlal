#include "multiplier.hpp"

#include <sstream>

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Multiplier; }

namespace dlal{

Multiplier::Multiplier(): _output(nullptr), _multiplier(1.0f) {}

bool Multiplier::ready(){ return _output; }

void Multiplier::addOutput(Component* output){
	if(!output->readAudio()){ _text="output must have audio"; return; }
	_output=output;
}

void Multiplier::evaluate(unsigned samples){
	for(unsigned i=0; i<samples; ++i) _output->readAudio()[i]*=_multiplier;
}

std::string* Multiplier::readText(){ return &_text; }

void Multiplier::clearText(){ _text.clear(); }

bool Multiplier::sendText(const std::string& text){
	std::stringstream ss(text);
	std::string s;
	ss>>s;
	if(s=="set") ss>>_multiplier;
	else return false;
	return true;
}

std::string Multiplier::commands(){ return "set"; }

}//namespace dlal
