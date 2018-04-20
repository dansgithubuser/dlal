#include "midichlorian.hpp"

DLAL_BUILD_COMPONENT_DEFINITION(Midichlorian)

namespace dlal{

Midichlorian::Midichlorian(){
	_checkMidi=true;
	registerCommand("logic", "<and, or, xor>", [this](std::stringstream& ss)->std::string{
		std::string s;
		ss>>s;
		if(s=="and") _logic=Logic::AND;
		else if(s=="or") _logic=Logic::OR;
		else if(s=="xor") _logic=Logic::XOR;
		else return "error: unknown logic \""+s+"\"";
		return "";
	});
}

void Midichlorian::evaluate(){
	if(_period&&phase()){
		for(auto output: _outputs){
			uint8_t start[]={0x80, 0x3c, 0x7f};
			output->midi(start, sizeof(start));
			uint8_t stop[]={0x90, 0x3c, 0x7f};
			output->midi(stop, sizeof(stop));
			_system->_reportQueue.write("midi "+componentToStr(this)+" "+componentToStr(output));
		}
	}
}

void Midichlorian::midi(const uint8_t* bytes, unsigned size){
}

}//namespace dlal
