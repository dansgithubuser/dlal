#include "pitcher.hpp"

#include <cmath>

DLAL_BUILD_COMPONENT_DEFINITION(Pitcher)

namespace dlal{

Pitcher::Pitcher(){
	_checkMidi=true;
	addJoinAction([this](System&){ _silence=_glissSeparation+1; return ""; });
	registerCommand("serialize_pitcher", "", [this](std::stringstream&){
		std::stringstream ss;
		ss<<_glissSeparation<<" "<<_glissRate<<" "<<_vibratoRate<<" "<<_vibratoAmount;
		return ss.str();
	});
	registerCommand("deserialize_pitcher", "<serialized>", [this](std::stringstream& ss){
		ss>>_glissSeparation>>_glissRate>>_vibratoRate>>_vibratoAmount;
		return "";
	});
	registerCommand("set_gliss_separation", "<separation in seconds>", [this](std::stringstream& ss){
		ss>>_glissSeparation;
		return "";
	});
	registerCommand("set_gliss_rate", "<gliss rate>", [this](std::stringstream& ss){
		ss>>_glissRate;
		return "";
	});
	registerCommand("set_vibrato_rate", "<vibrato rate>", [this](std::stringstream& ss){
		ss>>_vibratoRate;
		return "";
	});
	registerCommand("set_vibrato_amount", "<vibrato amount>", [this](std::stringstream& ss){
		ss>>_vibratoAmount;
		return "";
	});
}

std::string Pitcher::connect(Component& output){
	midiSend(&output, Midi{0xb0, 0x65,  0}.data(), 3);
	midiSend(&output, Midi{0xb0, 0x64,  0}.data(), 3);
	midiSend(&output, Midi{0xb0, 0x06, 64}.data(), 3);
	midiSend(&output, Midi{0xb0, 0x26,  0}.data(), 3);
	return MultiOut::connect(output);
}

std::string Pitcher::disconnect(Component& output){
	midiSend(&output, Midi{0xb0, 0x65,  0}.data(), 3);
	midiSend(&output, Midi{0xb0, 0x64,  0}.data(), 3);
	midiSend(&output, Midi{0xb0, 0x06,  2}.data(), 3);
	midiSend(&output, Midi{0xb0, 0x26,  0}.data(), 3);
	midiSend(&output, Midi{0xe0, 0x00, 0x20}.data(), 3);
	return MultiOut::disconnect(output);
}

void Pitcher::evaluate(){
	if(_off.size()) _silence+=_samplesPerEvaluation/float(_sampleRate);
	if(_silence>_glissSeparation&&_off.size()){
		for(auto output: _outputs)
			midiSend(output, _off.data(), 3);
		_off.clear();
	}
	_phase+=_samplesPerEvaluation/float(_sampleRate);
	_pitch=(_pitch+_glissRate*_pitchDst)/(1+_glissRate);
	uint16_t pitch=_pitch+0x80*_vibratoAmount*std::sin(_phase*_vibratoRate*2*3.14159f);
	for(auto output: _outputs)
		midiSend(output, Midi{0xe0, uint8_t(pitch&0x7fu), uint8_t(pitch>>7)}.data(), 3);
}

void Pitcher::midi(const uint8_t* bytes, unsigned size){
	if(size!=3) return;
	if(bytes[0]==0x90){
		if(bytes[2])
			noteOn(bytes);
		else
			noteOff(bytes);
	}
	else if(bytes[0]==0x80)
		noteOff(bytes);
}

void Pitcher::noteOn(const uint8_t* bytes){
	_pitchDst=0x2000+0x80*(bytes[1]-64);
	if(_silence>_glissSeparation){
		_pitch=_pitchDst;
		for(auto output: _outputs)
			midiSend(output, Midi{bytes[0], 64, bytes[2]}.data(), 3);
	}
	_on=bytes[1];
	_off.clear();
	_silence=0.0f;
}

void Pitcher::noteOff(const uint8_t* bytes){
	if(_on==bytes[1]){
		_off=Midi(bytes, bytes+3);
		_off[1]=64;
	}
}

}//namespace dlal
