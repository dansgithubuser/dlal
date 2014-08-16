#include "audio.hpp"

#include <iostream>

int main(){
	dlal::System system;
	dlal::Audio audio;
	system.addComponent(audio, "audio");
	audio.sendText("test");
	audio.sendText("start 44100 6");
	std::cout<<*audio.readText()<<"\n";
	std::string s;
	std::cin>>s;
	return 0;
}
