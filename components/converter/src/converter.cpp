#include "converter.hpp"

#include <obvious.hpp>

DLAL_BUILD_COMPONENT_DEFINITION(Converter)

namespace dlal{

Converter::Converter(): _controller(0){
	_checkMidi=true;
	addJoinAction([this](System&){
		_audio.resize(_samplesPerEvaluation, 0.0f);
		return "";
	});
	registerCommand("set", "<controller number>", [this](std::stringstream& ss){
		ss>>_controller;
		if(_controller>127){
			_controller=0;
			return "error: controller number too high";
		}
		return "";
	});
	registerCommand("serialize_converter", "", [this](std::stringstream& ss){
		return ::str(_controller);
	});
	registerCommand("deserialize_converter", "serialized", [this](std::stringstream& ss){
		::dstr(ss, _controller);
		return "";
	});
}

void Converter::evaluate(){
	uint8_t x[]={0xb0, _controller, uint8_t(64+_audio.back()*63)};
	for(auto output: _outputs) midiSend(output, x, sizeof(x));
	std::fill_n(_audio.data(), _samplesPerEvaluation, 0.0f);
}

}//namespace dlal
