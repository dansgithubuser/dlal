#include "page.hpp"

#include <cstring>
#include <iostream>

namespace dlal{

Page::Page(const float* audio, unsigned size, uint64_t evaluation):
	_type(AUDIO), _evaluation(evaluation), _audio(audio, audio+size)
{}

Page::Page(const uint8_t* midi, unsigned size, uint64_t evaluation):
	_type(MIDI), _evaluation(evaluation), _midi(midi, midi+size)
{}

Page::Page(const std::string& text, uint64_t evaluation):
	_type(TEXT), _evaluation(evaluation), _text(text)
{}

Page::Page(std::istream& file){
	unsigned type, size;
	if(!(file>>type)||!(file>>_evaluation)||!(file>>size)) return;
	switch(type){
		case AUDIO:
			_audio.resize(size);
			for(unsigned i=0; i<size; ++i)
				if(!(file>>_audio[i])) return;
			break;
		case MIDI:
			_midi.resize(size);
			for(unsigned i=0; i<size; ++i){
				unsigned byte;
				if(!(file>>byte)) return;
				_midi[i]=byte;
			}
			break;
		case TEXT:
			_text.resize(size);
			if(!file.ignore(1)||!file.read(&_text[0], size)) return;
			break;
		default: break;
	}
	_type=(Type)type;
}

void Page::toFile(std::ostream& file) const{
	file<<_type<<' ';
	file<<_evaluation<<' ';
	switch(_type){
		case AUDIO:
			file<<_audio.size()<<' ';
			for(auto i: _audio) file<<i<<' ';
			break;
		case MIDI:
			file<<_midi.size()<<' ';
			for(auto i: _midi) file<<(unsigned)i<<' ';
			break;
		case TEXT:
			file<<_text.size()<<' ';
			file<<_text;
			break;
		default: break;
	}
	file<<'\n';
}

void Page::dispatch(
	const Component& component,
	std::vector<Component*>& outputs,
	int samplesPerEvaluation
) const{
	switch(_type){
		case Page::NONE: break;
		case Page::AUDIO:
			safeAdd(_audio.data(), samplesPerEvaluation, outputs);
			break;
		case Page::MIDI:
			for(auto output: outputs){
				component.midiSend(output, _midi.data(), _midi.size());
			}
			break;
		case Page::TEXT:
			for(auto output: outputs){
				std::string result=output->command(_text);
				component._system->_reports.write((std::string)"command "+component._name+" "+output->_name);
			}
			break;
	}
}

}//namespace dlal
