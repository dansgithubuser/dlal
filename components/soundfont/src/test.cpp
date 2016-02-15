#include "soundfont.hpp"

#include <iostream>

int main(int argc, char** argv){
	dlalDyadInit();
	dlal::System system;
	dlal::Soundfont soundfont;
	dlal::Dummy dummy;
	if(argc<2){
		std::cout<<"usage: soundfont <soundfont file>\n";
		dlalDyadShutdown();
		return 0;
	}
	system.set(22050, 5);
	std::cout<<system.add(soundfont, 0);
	std::cout<<system.add(dummy, 0);
	std::cout<<soundfont.connect(dummy);
	std::cout<<soundfont.command("load "+std::string(argv[1]))<<"\n";
	while(true){
		std::string s;
		std::cin>>s;
		if(s=="q") break;
		else if(s=="a"){
			uint8_t midi[]={0x80, 60};
			soundfont.midi(midi, sizeof(midi));
		}
		else if(s=="z"){
			uint8_t midi[]={0x90, 60, 0x40};
			soundfont.midi(midi, sizeof(midi));
		}
		system.evaluate();
		for(unsigned i=0; i<dummy._audio.size(); ++i) std::cout<<dummy._audio[i]<<" ";
		std::cout<<"\n";
	}
	dlalDyadShutdown();
	return 0;
}
