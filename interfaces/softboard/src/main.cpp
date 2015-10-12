#include "softboard.hpp"
#include "dyad.hpp"

#include <SFML/Graphics.hpp>

#include <iostream>
#include <cstdlib>
#include <sstream>
#include <thread>
#include <chrono>

int main(int argc, char** argv){
	if(argc!=3){
		std::cerr<<"usage: Softboard ip port\n";
		return EXIT_FAILURE;
	}
	int port;
	std::stringstream ss;
	ss<<argv[2];
	ss>>port;
	if(!dyadInit(std::string(argv[1]), port)) return EXIT_FAILURE;
	Softboard softboard;
	sf::RenderWindow window(sf::VideoMode(160, 20), "dlal softboard");
	window.setKeyRepeatEnabled(false);
	int result=EXIT_SUCCESS;
	while(window.isOpen()){
		if(!dyadCheck()) window.close();
		sf::Event event;
		while(window.pollEvent(event)){
			switch(event.type){
				case sf::Event::KeyPressed:
				case sf::Event::KeyReleased:
					if(!dyadWrite(softboard.processKey(
						event.key.code,
						event.type==sf::Event::KeyPressed
					))){
						result=EXIT_FAILURE;
						window.close();
					}
					break;
				case sf::Event::Closed:
					window.close();
					break;
				default: break;
			}
			window.clear();
			window.display();
		}
		std::this_thread::sleep_for(std::chrono::milliseconds(1));
	}
	if(!dyadFinish()) return EXIT_FAILURE;
	return result;
}
