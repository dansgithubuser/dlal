#include <soundfont.hpp>

DLAL_BUILD_COMPONENT_DEFINITION(Soundfont)

namespace dlal{

Soundfont::Soundfont(): _settings(NULL), _synth(NULL) {
	_checkAudio=true;
	addJoinAction([this](System&){
		return initialize();
	});
	registerCommand("load", "<soundfont file>", [this](std::stringstream& ss){
		std::string s;
		s=initialize();
		if(isError(s)) return s;
		ss>>s;
		return std::to_string(fluid_synth_sfload(_synth, s.c_str(), 1));
	});
}

Soundfont::~Soundfont(){ destroy(); }

void Soundfont::evaluate(){
	fluid_synth_write_float(_synth, _samplesPerEvaluation, _l.data(), 0, 1, _r.data(), 0, 1);
	add(_l.data(), _samplesPerEvaluation, _outputs);
	add(_r.data(), _samplesPerEvaluation, _outputs);
}

void Soundfont::midi(const uint8_t* bytes, unsigned size){
	if(!size) return;
	uint8_t command=bytes[0]&0xf0;
	uint8_t channel=bytes[0]&0x0f;
	switch(command){
		case 0x80:
			if(size<2) break;
			fluid_synth_noteoff(_synth, channel, bytes[1]);
			break;
		case 0x90:
			if(size<3) break;
			fluid_synth_noteon(_synth, channel, bytes[1], bytes[2]);
			break;
		case 0xc0:
			if(size<2) break;
			fluid_synth_program_change(_synth, channel, bytes[1]);
			break;
		default: break;
	}
}

void Soundfont::destroy(){
	if(!_settings) return;
	delete_fluid_synth(_synth);
	delete_fluid_settings(_settings);
	_synth=NULL;
	_settings=NULL;
}

std::string Soundfont::initialize(){
	if(_settings) return "";
	if(!_sampleRate) return "error: sample rate not set";
	if(!_samplesPerEvaluation) return "error: samples per evaluation not set";
	_settings=new_fluid_settings();
	fluid_settings_setint(_settings, "synth.samplerate", _sampleRate);
	_synth=new_fluid_synth(_settings);
	_l.resize(_samplesPerEvaluation);
	_r.resize(_samplesPerEvaluation);
	return "";
}

}//namespace dlal
