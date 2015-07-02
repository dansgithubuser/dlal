#include "page.hpp"

#include <cstring>

namespace dlal{

Page::Page(const float* audio, unsigned size, uint64_t evaluation):
	_type(AUDIO), _audio(audio, audio+size), _evaluation(evaluation)
{}

Page::Page(const uint8_t* midi, unsigned size, uint64_t evaluation):
	_type(MIDI), _midi(midi, midi+size), _evaluation(evaluation)
{}

Page::Page(const std::string& text, uint64_t evaluation):
	_type(TEXT), _text(text), _evaluation(evaluation)
{}

Page::Page(std::istream& file){
	unsigned type;
	file>>type;
	_type=(Type)type;
	file>>_evaluation;
	unsigned size;
	file>>size;
	switch(_type){
		case AUDIO:
			_audio.resize(size);
			for(unsigned i=0; i<size; ++i) file>>_audio[i];
			break;
		case MIDI:
			_midi.resize(size);
			for(unsigned i=0; i<size; ++i){
				unsigned byte;
				file>>byte;
				_midi[i]=byte;
			}
			break;
		case TEXT:
			_text.resize(size);
			file.ignore(1);
			file.read(&_text[0], size);
			break;
		default: break;
	}
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
}

void Page::dispatch(
	int samplesPerEvaluation, std::vector<Component*>& outputs
) const{
	switch(_type){
		case Page::AUDIO:
			safeAdd(_audio.data(), samplesPerEvaluation, outputs);
			break;
		case Page::MIDI:
			for(auto output: outputs) output->midi(_midi.data(), _midi.size());
			break;
		case Page::TEXT:
			for(auto output: outputs) output->command(_text);
			break;
	}
}

}//namespace dlal
