#include "arpeggiator.hpp"

DLAL_BUILD_COMPONENT_DEFINITION(Arpeggiator)

namespace dlal{

Arpeggiator::Arpeggiator(): _i(0), _evaluation(0), _evaluationsPerNote(25.0f){
	_checkMidi=true;
	registerCommand("set", "<evaluations per note>", [this](std::stringstream& ss){
		ss>>_evaluationsPerNote;
		return "";
	});
	_nameToControl["e"]=&_evaluationsPerNote;
}

void Arpeggiator::evaluate(){
	++_evaluation;
	if(_evaluation>=_evaluationsPerNote){
		_evaluation-=int(_evaluationsPerNote);
		if(_down.size()){
			++_i;
			_i%=_down.size();
			auto i=_down.begin();
			for(unsigned j=0; j<_i; ++j) ++i;
			uint8_t x[]={0x80, _sounding.first, _sounding.second};
			uint8_t y[]={0x90, i->first, i->second};
			for(auto output: _outputs){
				midiSend(output, x, sizeof(x));
				midiSend(output, y, sizeof(y));
			}
			_sounding=std::make_pair(i->first, i->second);
		}
		else{
			_i=0;
			uint8_t x[]={0x80, _sounding.first, _sounding.second};
			for(auto output: _outputs) midiSend(output, x, sizeof(x));
		}
	}
}

void Arpeggiator::midi(const uint8_t* bytes, unsigned size){
	MidiControllee::midi(bytes, size);
	if(!size) return;
	uint8_t command=bytes[0]&0xf0;
	switch(command){
		case 0x80:
			if(size<2) break;
			_down.erase(bytes[1]);
			break;
		case 0x90:
			if(size<3) break;
			if(bytes[2]==0) _down.erase(bytes[1]);
			else _down[bytes[1]]=bytes[2];
			break;
		default: break;
	}
}

}//namespace dlal
