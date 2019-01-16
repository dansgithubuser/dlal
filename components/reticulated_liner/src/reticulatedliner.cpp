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
	for(unsigned i=0; i<2; ++i){
		for(auto output: _outputs) midiSend(output, _iterator->data(), _iterator->size());
		++_iterator;
		if(!_iterator){
			_line.freshen();
			_iterator=_line.begin();
		}
		if((_iterator->at(0)&0xf0)==0x80) break;
	}
}

Midi ReticulatedLiner::getMidi() const {
	dlal::Midi result;
	for(auto i: _line) result.append(1, result.ticksPerQuarter, i);
	return result;
}

std::string ReticulatedLiner::putMidi(Midi midi){
	if(midi.tracks.size()<2) return "error: no track to read";
	auto pairs=getPairs(midi.tracks[1]);
	_line.clear();
	for(auto i: pairs) _line.push_back(i.event);
	return "";
}

}//namespace dlal
