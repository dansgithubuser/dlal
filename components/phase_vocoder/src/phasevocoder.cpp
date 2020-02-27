#include "phasevocoder.hpp"

DLAL_BUILD_COMPONENT_DEFINITION(PhaseVocoder)

extern "C" {
	void* construct(const char* kind, double sampleRate, uint32_t bins, uint32_t timeDiv);
	void destruct(void* plugin);
	void run(void* plugin, float* audio, uint32_t size);
}

namespace dlal{

PhaseVocoder::PhaseVocoder(){
	_maxOutputs=1;
	registerCommand("become", "kind [bins=128] [timeDiv=4]", [this](std::stringstream& ss){
		std::string kind;
		unsigned bins=512, timeDiv=4;
		ss>>kind>>bins>>timeDiv;
		if(plugin) destruct(plugin);
		plugin=construct(kind.c_str(), (double)_sampleRate, bins, timeDiv);
		return "";
	});
}

PhaseVocoder::~PhaseVocoder(){
	if(!plugin) return;
	destruct(plugin);
}

void PhaseVocoder::evaluate(){
	if(!plugin) return;
	for(auto& i: _outputs)
		run(plugin, i->audio(), (uint32_t)_samplesPerEvaluation);
}

}//namespace dlal
