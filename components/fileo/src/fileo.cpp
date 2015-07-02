#include "fileo.hpp"

#include <chrono>

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Fileo; }

namespace dlal{

Fileo::Fileo(): _evaluation(0), _queue(8), _audioRead(false), _quit(false) {
	addJoinAction([this](System&){
		if(!_file.is_open()) return "error: output file not set!";
		_audio.resize(_samplesPerEvaluation, 0.0f);
		_thread=std::thread([this](){
			Page page;
			while(!_quit){
				std::this_thread::sleep_for(std::chrono::milliseconds(1));
				while(_queue.read(page, true)) page.toFile(_file);
			}
			while(_queue.read(page, true)) page.toFile(_file);
		});
		return "";
	});
	registerCommand("name", "<output file name>", [this](std::stringstream& ss){
		std::string fileName;
		ss>>fileName;
		_file.open(fileName.c_str());
		if(!_file.is_open()) return "Couldn't open file!";
		return "";
	});
	registerCommand("finish", "", [this](std::stringstream&){
		finish();
		return "";
	});
}

Fileo::~Fileo(){ finish(); }

std::string Fileo::command(const std::string& command){
	if(_file.is_open()&&command.compare(0, 6, "finish"))
		_queue.write(Page(command, _evaluation));
	return Component::command(command);
}

void Fileo::evaluate(){
	if(_audioRead){
		_queue.write(Page(_audio.data(), _audio.size(), _evaluation));
		std::fill_n(_audio.data(), _audio.size(), 0.0f);
		_audioRead=false;
	}
	++_evaluation;
}

void Fileo::midi(const uint8_t* bytes, unsigned size){
	_queue.write(Page(bytes, size, _evaluation));
}

float* Fileo::audio(){
	_audioRead=true;
	return _audio.data();
}

void Fileo::finish(){
	_quit=true;
	if(_thread.joinable()) _thread.join();
	_file.close();
}

}//namespace dlal
