#include "lpf.hpp"

#include <cmath>

DLAL_BUILD_COMPONENT_DEFINITION(Lpf)

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

void Lpf::midi(const uint8_t* bytes, unsigned size){
	if(size==3&&(bytes[0]>>4)==9){
		const int note=bytes[1];
		const float f=440*std::pow(2, (note-69)/12.0f);
		_lowness=1/(2*3.14159f/_sampleRate*f+1);
	}
}

}//namespace dlal
