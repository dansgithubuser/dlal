#include "soundfont.hpp"

#include <iostream>

int main(int argc, char** argv){
	dlal::System system;
	dlal::Soundfont soundfont;
	dlal::Dummy dummy;
	if(argc<2){
		std::cout<<"usage: soundfont <soundfont file>\n";
		return 0;
	}
	system.set(22050, 8);
	std::cout<<system.add(soundfont, 0)<<"...\n";
	std::cout<<system.add(dummy, 0)<<"...\n";
	std::cout<<soundfont.connect(dummy)<<"...\n";
	std::cout<<soundfont.command("load "+std::string(argv[1]))<<"...\n";
	unsigned reps=1;
	while(true){
		std::string s;
		std::cin>>s;
		if(s=="q") break;
		else if(s=="x"){
			std::cin>>reps;
		}
		else if(s=="a"){
			uint8_t midi[]={0x80, 60, 0x7f};
			soundfont.midi(midi, sizeof(midi));
		}
		else if(s=="z"){
			uint8_t midi[]={0x90, 60, 0x7f};
			soundfont.midi(midi, sizeof(midi));
		}
		for(unsigned rep=0; rep<reps; ++rep){
			system.evaluate();
			for(unsigned i=0; i<dummy._audio.size(); ++i) std::cout<<dummy._audio[i]<<" ";
			std::cout<<"\n";
		}
		reps=1;
	}
	return 0;
}
