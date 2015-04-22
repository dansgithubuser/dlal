#include "multiplier.hpp"

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Multiplier; }

namespace dlal{

Multiplier::Multiplier(): _output(nullptr), _multiplier(1.0f) {
	registerCommand("set", "multiplier", [&](std::stringstream& ss){
		ss>>_multiplier;
		return "";
	});
}

std::string Multiplier::addOutput(Component* output){
	if(!output->readAudio()) return "error: output must have audio";
	_output=output;
	return "";
}

std::string Multiplier::readyToEvaluate(){
	if(!_output) return "error: output not set";
	return "";
}

void Multiplier::evaluate(unsigned samples){
	for(unsigned i=0; i<samples; ++i) _output->readAudio()[i]*=_multiplier;
}

}//namespace dlal
