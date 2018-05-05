#include "reverb.hpp"

DLAL_BUILD_COMPONENT_DEFINITION(Reverb)

namespace dlal{

Reverb::Reverb(){
	_checkAudio=true;
	_echos.push_back(ModRingbuffer<float>(2239, 0.0f));
	_echos.push_back(ModRingbuffer<float>(3217, 0.0f));
	_echos.push_back(ModRingbuffer<float>(4409, 0.0f));
	_echos.push_back(ModRingbuffer<float>(5003, 0.0f));
	_echos.push_back(ModRingbuffer<float>(6689, 0.0f));
	_echos.push_back(ModRingbuffer<float>(7057, 0.0f));
	registerCommand("set", "<reverb amount (0..1)>", [this](std::stringstream& ss){
		ss>>_amount;
		_amount/=_echos.size();
		return "";
	});
	command("set 0.5");
}

void Reverb::evaluate(){
	if(!_outputs.size()) return;
	auto output=_outputs[0];
	for(unsigned i=0; i<_samplesPerEvaluation; ++i){
		for(unsigned j=0; j<_echos.size(); ++j) output->audio()[i]+=_echos[j].read(0)*_amount;
		for(auto& echo: _echos) echo.write(output->audio()[i]);
	}
}

}//namespace dlal
