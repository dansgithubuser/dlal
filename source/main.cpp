#include "audio.hpp"
#include "midi.hpp"

#include <iostream>
#include <string>

const unsigned LOG2_SAMPLES_PER_CALLBACK=6;
const unsigned SAMPLES_PER_CALLBACK=1<<LOG2_SAMPLES_PER_CALLBACK;

int main(int argc, char** argv){
	dlal::audioInit(
		[](const float* input, float* output){
			for(unsigned i=0; i<SAMPLES_PER_CALLBACK; ++i)
				output[i]=input[i];
		},
		44100,
		LOG2_SAMPLES_PER_CALLBACK
	);
	dlal::midiInit(
		[](std::vector<unsigned char>& message){
		}
	);
	std::cout<<"started\n";
	std::string s;
	std::cin>>s;
	dlal::midiFinish();
	dlal::audioFinish();
	return 0;
}
