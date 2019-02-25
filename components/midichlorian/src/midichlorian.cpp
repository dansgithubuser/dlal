#include "midichlorian.hpp"

DLAL_BUILD_COMPONENT_DEFINITION(Midichlorian)

namespace dlal{

Midichlorian::Midichlorian(){
	_checkMidi=true;
	_period=44100;
	addJoinAction([this](System&){
		_phase=_period;
		return "";
	});
	registerCommand("rhythm", "<x for note, . for rest>", [this](std::stringstream& ss)->std::string{
		std::string s;
		ss>>s;
		for(auto c: s) if(c!='.'&&c!='x') return "error: invalid character in rhythm";
		_rhythm=s;
		_i=0;
		return "";
	});
	registerCommand("serialize_midichlorian", "", [this](std::stringstream&){
		return _rhythm;
	});
	registerCommand("deserialize_midichlorian", "<serialized>", [this](std::stringstream& ss){
		std::string s;
		ss>>s;
		return command("rhythm "+s);
	});
}

void Midichlorian::evaluate(){
	if(_period&&phase()){
		for(auto output: _outputs){
			uint8_t stop[]={0x80, 0x3c, 0x7f};
			midiSend(output, stop, sizeof(stop));
			if(_rhythm[_i]=='x'){
				uint8_t start[]={0x90, 0x3c, 0x7f};
				midiSend(output, start, sizeof(start));
			}
			++_i;
			_i%=_rhythm.size();
		}
	}
}

}//namespace dlal
