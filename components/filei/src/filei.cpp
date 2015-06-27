#include "filei.hpp"

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Filei; }

namespace dlal{

Filei::Filei(): _evaluation(0), _index(0) {
	_emptyAudio.resize(1, 0.0f);
	reset();
	registerCommand("name", "<input file name>", [&](std::stringstream& ss){
		std::string fileName;
		ss>>fileName;
		std::ifstream file(fileName.c_str());
		if(!file.good()) return "error: couldn't open file!";
		_loaded.clear();
		while(file.peek()!=EOF){
			Page page;
			page.fromFile(file);
			_loaded.push_back(page);
		}
		return "";
	});
	registerCommand("resize", "<samples per callback>", [&](std::stringstream& ss){
		unsigned samplesPerCallback;
		ss>>samplesPerCallback;
		_emptyAudio.resize(samplesPerCallback);
		return "";
	});
}

std::string Filei::readyToEvaluate(){
	if(_emptyAudio.size()==1) return "error: samples per callback not set!";
	if(_loaded.empty()) return "error: no file loaded!";
	return "";
}

void Filei::evaluate(unsigned samples){
	reset();
	while(_index<_loaded.size()&&_loaded[_index]._evaluation<=_evaluation){
		switch(_loaded[_index]._type){
			case Page::AUDIO: _audio=_loaded[_index]._audio.data(); break;
			case Page::MIDI: _midi=&_loaded[_index]._midi; break;
			case Page::TEXT: _text=&_loaded[_index]._text; break;
			default: break;
		}
		++_index;
	}
	++_evaluation;
}

float* Filei::readAudio(){ return _audio; }
MidiMessages* Filei::readMidi(){ return _midi; }
std::string* Filei::readText(){ return _text; }

void Filei::reset(){
	_audio=_emptyAudio.data();
	_midi=&_emptyMidi;
	_text=&_emptyText;
}

}//namespace dlal
