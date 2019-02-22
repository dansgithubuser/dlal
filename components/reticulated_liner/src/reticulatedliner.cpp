#include "reticulatedliner.hpp"

DLAL_BUILD_COMPONENT_DEFINITION(ReticulatedLiner)

namespace dlal{

ReticulatedLiner::ReticulatedLiner(): _line(256) {
	_iterator=_line.begin();
	_checkMidi=true;
	registerCommand("save", "<file path>", [this](std::stringstream& ss){
		std::string filePath;
		ss>>filePath;
		getMidi().write(filePath);
		return "";
	});
	registerCommand("load", "<file path>", [this](std::stringstream& ss){
		std::string filePath;
		ss>>filePath;
		dlal::Midi midi;
		midi.read(filePath);
		return putMidi(midi);
	});
	registerCommand("add_reticule", "<midi bytes>", [this](std::stringstream& ss){
		Reticule r;
		std::vector<uint8_t> bytes;
		unsigned byte;
		while(ss>>byte){
			if((byte&0x80)&&bytes.size()){
				r.push_back(bytes);
				bytes.clear();
			}
			bytes.push_back(byte);
		}
		if(bytes.size()) r.push_back(bytes);
		_line.push_back(r);
		return "";
	});
	registerCommand("clear", "", [this](std::stringstream& ss){
		_line.clear();
		return "";
	});
	registerCommand("serialize_reticulated_liner", "", [this](std::stringstream&){
		auto midi=getMidi();
		std::vector<uint8_t> bytes;
		midi.write(bytes);
		std::stringstream ss;
		ss<<bytes;
		return ss.str();
	});
	registerCommand("deserialize_reticulated_liner", "<serialized>", [this](std::stringstream& ss){
		std::vector<uint8_t> bytes;
		ss>>bytes;
		dlal::Midi midi;
		midi.read(bytes);
		return putMidi(midi);
	});
}

void ReticulatedLiner::midi(const uint8_t* bytes, unsigned size){
	if(size!=3||(bytes[0]&0xf0)!=0x90) return;
	if(!_iterator) _iterator=_line.begin();
	if(!_iterator) return;
	while(true){
		if(_iterator->size())
			for(auto output: _outputs)
				for(const auto& i: *_iterator)
					midiSend(output, i.data(), i.size());
		++_iterator;
		if(!_iterator){
			_line.freshen();
			_iterator=_line.begin();
		}
		else break;
	}
}

Midi ReticulatedLiner::getMidi() const {
	dlal::Midi result;
	int delta=0;
	for(auto i: _line){
		for(auto j: i){
			result.append(1, delta, j);
			delta=0;
		}
		delta+=result.ticksPerQuarter;
	}
	return result;
}

std::string ReticulatedLiner::putMidi(Midi midi){
	if(midi.tracks.size()<2) return "error: no track to read";
	auto pairs=getPairs(midi.tracks[1]);
	_line.clear();
	Reticule reticule;
	for(auto i: pairs){
		if(i.delta){
			_line.push_back(reticule);
			reticule.clear();
		}
		for(auto j=midi.ticksPerQuarter; j<i.delta; j+=midi.ticksPerQuarter)
			_line.push_back(Reticule());
		reticule.push_back(i.event);
	}
	_line.push_back(reticule);
	return "";
}

}//namespace dlal
