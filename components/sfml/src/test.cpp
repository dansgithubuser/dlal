#include "sfml.hpp"

#include <thread>
#include <atomic>
#include <string>
#include <iostream>
#include <cstdlib>
#include <ctime>

int main(){
	dlal::Sfml sfml;
	std::atomic<bool> quit(false);
	std::srand(std::time(NULL));
	std::thread thread([&](){
		while(!quit){
			sfml.evaluate(0);
			dlal::MidiMessages& messages=*sfml.readMidi();
			for(unsigned i=0; i<messages.size(); ++i){
				for(unsigned j=0; j<dlal::MidiMessage::SIZE; ++j)
					std::cout<<std::hex<<(unsigned)messages[i]._bytes[j]<<" ";
				std::cout<<"\n";
			}
			sf::sleep(sf::milliseconds(rand()%50));
		}
	});
	std::string s;
	std::cin>>s;
	quit=true;
	thread.join();
	return 0;
}
