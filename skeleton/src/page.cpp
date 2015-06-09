#include "page.hpp"

#include <cstring>

namespace dlal{

bool Page::fromAudio(float* audio, unsigned size, uint64_t evaluation){
	if(!audio) return false;
	_type=AUDIO;
	_evaluation=evaluation;
	_audio.resize(size);
	std::memcpy(_audio.data(), audio, size*sizeof(*audio));
	return true;
}

bool Page::fromMidi(MidiMessages* midi, uint64_t evaluation){
	if(!midi||!midi->size()) return false;
	_type=MIDI;
	_evaluation=evaluation;
	_midi=*midi;
	return true;
}

bool Page::fromText(std::string* text, uint64_t evaluation){
	if(!text||!text->size()) return false;
	_type=TEXT;
	_evaluation=evaluation;
	_text=*text;
	return true;
}

void Page::toFile(std::ostream& file){
	file<<_type<<' ';
	switch(_type){
		case AUDIO:
			file<<_audio.size()<<' ';
			for(unsigned i=0; i<_audio.size(); ++i) file<<_audio[i]<<' ';
			break;
		case MIDI:{
			std::vector<uint8_t> bytes;
			_midi.serialize(bytes);
			file<<bytes.size()<<' ';
			for(unsigned i=0; i<bytes.size(); ++i) file<<(unsigned)bytes[i]<<' ';
			break;
		}
		case TEXT:
			file<<_text.size()<<' ';
			file<<_text;
			break;
		default: break;
	}
}

void Page::fromFile(std::istream& file){
	unsigned type;
	file>>type;
	_type=(Type)type;
	unsigned size;
	file>>size;
	switch(_type){
		case AUDIO:
			_audio.resize(size);
			for(unsigned i=0; i<size; ++i) file>>_audio[i];
			break;
		case MIDI:{
			std::vector<uint8_t> bytes(size);
			for(unsigned i=0; i<size; ++i){
				unsigned byte;
				file>>byte;
				bytes[i]=byte;
			}
			_midi.deserialize(bytes);
			break;
		}
		case TEXT:
			_text.resize(size);
			file.ignore(1);
			file.read(&_text[0], size);
			break;
		default: break;
	}
}

}//namespace dlal
