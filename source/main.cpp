#include "audio.hpp"
#include "midi.hpp"
#include "fm.hpp"
#include "processor.hpp"

#include <iostream>
#include <string>

const unsigned LOG2_SAMPLES_PER_CALLBACK=6;
const unsigned SAMPLES_PER_CALLBACK=1<<LOG2_SAMPLES_PER_CALLBACK;
const unsigned SAMPLE_RATE=44100;

void printHelp(){
	std::cout<<"Enter Help to print this text."<<std::endl;
	std::cout<<"Enter Quit to quit."<<std::endl;
	std::cout<<std::endl;
}

int main(int argc, char** argv){
	dlal::Processor processor(SAMPLE_RATE, SAMPLES_PER_CALLBACK, std::cout);
	dlal::audioInit(
		[&](const float* input, float* output){
			processor.processMic(input);
			processor.output(output);
		},
		SAMPLE_RATE,
		LOG2_SAMPLES_PER_CALLBACK
	);
	dlal::midiInit([&](std::vector<unsigned char>& message){
		processor.processMidi(message);
	});
	printHelp();
	while(true){
		std::string s;
		std::cout<<">";
		std::getline(std::cin, s);
		if(s=="Quit") break;
		else if(s=="Help") printHelp();
		else processor.processText(s);
	}
	dlal::midiFinish();
	dlal::audioFinish();
	return 0;
}
