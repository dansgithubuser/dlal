#include "audio.hpp"

#include <iostream>

int main(){
	dlalDyadInit();
	dlal::System system;
	dlal::Audio audio;
	std::cout<<audio.command("test");
	std::cout<<audio.command("set 44100 6");
	std::cout<<system.add(audio, 0);
	std::cout<<audio.command("start");
	std::string s;
	std::cin>>s;
	std::cout<<audio.command("finish");
	dlalDyadShutdown();
	return 0;
}
