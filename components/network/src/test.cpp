#include "network.hpp"

#include <midiMessages.hpp>

#include <iostream>
#include <cstdlib>
#include <thread>
#include <chrono>
#include <string>

int main(int argc, char** argv){
	if(argc!=2){
		std::cerr<<"usage: Network port\n";
		return EXIT_FAILURE;
	}
	dlal::Network network;
	network.sendCommand("open "+std::string(argv[1]));
	bool quit=false;
	std::thread thread([&](){
		while(!quit){
			network.evaluate(64);
			dlal::MidiMessages& messages=*network.readMidi();
			for(unsigned i=0; i<messages.size(); ++i){
				for(unsigned j=0; j<dlal::MidiMessage::SIZE; ++j)
					std::cout<<std::hex<<(unsigned)messages[i]._bytes[j]<<" ";
				std::cout<<std::endl;
			}
			std::this_thread::sleep_for(std::chrono::milliseconds(1));
		}
	});
	std::string s;
	std::cin>>s;
	quit=true;
	thread.join();
	return EXIT_SUCCESS;
}
