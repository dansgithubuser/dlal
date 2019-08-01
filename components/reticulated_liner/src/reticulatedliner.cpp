#include "reticulatedliner.hpp"

#include <obvious.hpp>

DLAL_BUILD_COMPONENT_DEFINITION(ReticulatedLiner)

namespace dlal{

ReticulatedLiner::ReticulatedLiner(){
	_index=0;
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
		dans::Midi midi;
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
		_index=0;
		return "";
	});
	registerCommand("clear", "", [this](std::stringstream& ss){
		_line.clear();
		_index=0;
		return "";
	});
	registerCommand("get_midi", "", [this](std::stringstream&){
		auto midi=getMidi();
		std::vector<uint8_t> bytes;
		midi.write(bytes);
		return ::str(bytes);
	});
	registerCommand("put_midi", "bytes", [this](std::stringstream& ss){
		std::vector<uint8_t> bytes;
		unsigned u;
		while(ss>>u) bytes.push_back(u);
		dans::Midi midi;
		midi.read(bytes);
		return putMidi(midi);
	});
	registerCommand("serialize_reticulated_liner", "", [this](std::stringstream&){
		return command("get_midi");
	});
	registerCommand("deserialize_reticulated_liner", "<serialized>", [this](std::stringstream& ss){
		std::vector<uint8_t> bytes;
		::dstr(ss, bytes);
		dans::Midi midi;
		midi.read(bytes);
		return putMidi(midi);
	});
}

void ReticulatedLiner::midi(const uint8_t* bytes, unsigned size){
	if(size!=3||(bytes[0]&0xf0)!=0x90) return;
	if(_index==_line.size()) _index=0;
	if(_index==_line.size()) return;
	while(true){
		if(_line[_index].size())
			for(auto output: _outputs)
				for(const auto& i: _line[_index])
					midiSend(output, i.data(), i.size());
		++_index;
		if(_index==_line.size()){
			_index=0;
		}
		else break;
	}
}

dans::Midi ReticulatedLiner::getMidi() const {
	dans::Midi result;
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

std::string ReticulatedLiner::putMidi(dans::Midi midi){
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
	_index=0;
	return "";
}

}//namespace dlal
