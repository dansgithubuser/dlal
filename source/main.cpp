#include "audio.hpp"
#include "midi.hpp"
#include "fm.hpp"
#include "queue.hpp"

#include <iostream>
#include <string>
#include <array>

const unsigned LOG2_SAMPLES_PER_CALLBACK=6;
const unsigned SAMPLES_PER_CALLBACK=1<<LOG2_SAMPLES_PER_CALLBACK;
const unsigned SAMPLE_RATE=44100;

int main(int argc, char** argv){
	dlal::Queue<std::vector<unsigned char>> queue(128);
	float samples[SAMPLES_PER_CALLBACK];
	for(unsigned i=0; i<SAMPLES_PER_CALLBACK; ++i)
		samples[i]=0.0f;
	dlal::Sonic sonic(samples, SAMPLE_RATE);
	dlal::audioInit(
		[&](const float* input, float* output){
			while(queue.read()){
				sonic.processMidi(*queue.read());
				queue.nextRead();
			}
			for(unsigned i=0; i<SAMPLES_PER_CALLBACK; ++i) samples[i]=0.0f;
			sonic.evaluate(SAMPLES_PER_CALLBACK);
			for(unsigned i=0; i<SAMPLES_PER_CALLBACK; ++i){
				output[i]=input[i]+samples[i];
			}
		},
		SAMPLE_RATE,
		LOG2_SAMPLES_PER_CALLBACK
	);
	dlal::midiInit(
		[&](std::vector<unsigned char>& message){
			*queue.write()=message;
			queue.nextWrite();
		}
	);
	while(true){
		std::string s;
		std::cin>>s;
		if(s=="q") break;
		std::vector<unsigned char> message;
		message.push_back(0x90);
		message.push_back(69-9);
		message.push_back(64);
		*queue.write()=message;
		queue.nextWrite();
	}
	dlal::midiFinish();
	dlal::audioFinish();
	return 0;
}
