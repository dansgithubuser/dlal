#include "fileo.hpp"

#include <chrono>

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Fileo; }

namespace dlal{

Fileo::Fileo(): _evaluation(0), _input(nullptr), _queue(8), _quit(false) {
	registerCommand("name", "<output file name>", [&](std::stringstream& ss){
		std::string fileName;
		ss>>fileName;
		_file.open(fileName.c_str());
		if(!_file.good()) return "Couldn't open file!";
		return "";
	});
}

Fileo::~Fileo(){
	_quit=true;
	_thread.join();
}

std::string Fileo::addInput(Component* input){
	if(_input) return "error: input already set!";
	_input=input;
	return "";
}

std::string Fileo::readyToEvaluate(){
	if(!_file.good()) return "error: output file not set!";
	if(!_input) return "error: input not set!";
	_thread=std::thread([&](){
		Page page;
		while(!_quit){
			std::this_thread::sleep_for(std::chrono::milliseconds(1));
			while(_queue.read(page, true)) page.toFile(_file);
		}
		while(_queue.read(page, true)) page.toFile(_file);
	});
	return "";
}

void Fileo::evaluate(unsigned samples){
	Page page;
	if(page.fromAudio(_input->readAudio(), samples, _evaluation)) _queue.write(page);
	if(page.fromMidi(_input->readMidi(), _evaluation)) _queue.write(page);
	if(page.fromText(_input->readText(), _evaluation)) _queue.write(page);
	++_evaluation;
}

}//namespace dlal
