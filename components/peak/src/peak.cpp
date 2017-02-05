#include "peak.hpp"

#include <algorithm>
#include <cmath>

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Peak; }

namespace dlal{

Peak::Peak():
	_decay(0.99f),
	_invertCoefficient(0.0f),
	_invertOffset(0.1f),
	_coefficient(1.0f)
{
	_checkAudio=true;
	registerCommand("decay", "decay", [this](std::stringstream& ss){
		ss>>_decay;
		return "";
	});
	registerCommand("invert_coefficient", "<invert coefficient>", [this](std::stringstream& ss){
		ss>>_invertCoefficient;
		return "";
	});
	registerCommand("invert_offset", "<invert offset>", [this](std::stringstream& ss){
		ss>>_invertOffset;
		return "";
	});
	registerCommand("coefficient", "coefficient", [this](std::stringstream& ss){
		ss>>_coefficient;
		return "";
	});
}

void Peak::evaluate(){
	for(auto output: _outputs){
		float& peak=_peak[output]._;
		for(unsigned i=0; i<_samplesPerEvaluation; ++i){
			peak*=_decay;
			float& y=output->audio()[i];
			peak=std::max(peak, std::abs(y));
			y=_invertCoefficient/(peak+_invertOffset)+_coefficient*peak;
		}
	}
}

}//namespace dlal
