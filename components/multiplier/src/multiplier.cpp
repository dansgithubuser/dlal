#include "multiplier.hpp"

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Multiplier; }

namespace dlal{

Multiplier::Multiplier(): _multiplier(1.0f) {
	_checkAudio=true;
	registerCommand("set", "multiplier", [this](std::stringstream& ss){
		ss>>_multiplier;
		return "";
	});
}

void Multiplier::evaluate(){
	for(auto output: _outputs)
		for(unsigned i=0; i<_samplesPerEvaluation; ++i)
			output->audio()[i]*=_multiplier;
}

}//namespace dlal
