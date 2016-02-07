#include "lpf.hpp"

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Lpf; }

namespace dlal{

Lpf::Lpf(): _lowness(0.5f) {
	_checkAudio=true;
	registerCommand("set", "lowness", [this](std::stringstream& ss){
		ss>>_lowness;
		return "";
	});
	_nameToControl["lowness"]=&_lowness;
}

void Lpf::evaluate(){
	for(auto output: _outputs){
		float& y1=_y[output]._;
		for(unsigned i=0; i<_samplesPerEvaluation; ++i){
			float& y2=output->audio()[i];
			y2=(1-_lowness)*y2+_lowness*y1;
			y1=y2;
		}
	}
}

}//namespace dlal
