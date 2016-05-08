#include "multiplier.hpp"

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Multiplier; }

namespace dlal{

Multiplier::Multiplier(): _multiplier(1.0f), _offset(0.0f), _gate(-1.0f) {
	_checkAudio=true;
	registerCommand("set", "multiplier", [this](std::stringstream& ss){
		ss>>_multiplier;
		return "";
	});
	registerCommand("offset", "<offset (amplitude)>", [this](std::stringstream& ss){
		ss>>_offset;
		return "";
	});
	registerCommand("gate", "<gate (amplitude)>", [this](std::stringstream& ss){
		ss>>_gate;
		return "";
	});
}

void Multiplier::evaluate(){
	if(_outputs.empty()) return;
	for(unsigned i=0; i<_samplesPerEvaluation; ++i)
		_outputs[0]->audio()[i]*=_multiplier;
	for(unsigned j=1; j<_outputs.size(); ++j)
		for(unsigned i=0; i<_samplesPerEvaluation; ++i){
			if(_outputs[j-1]->audio()[i]>_gate)
				_outputs[j]->audio()[i]*=_outputs[j-1]->audio()[i]+_offset;
			else
				_outputs[j]->audio()[i]=0.0f;
		}
}

}//namespace dlal
