#include "softboard.hpp"
#include "dyad.hpp"

#include <courierCode.hpp>

#include <SFML/Graphics.hpp>

#include <iostream>
#include <cstdlib>
#include <sstream>
#include <thread>
#include <chrono>
#include <set>

int main(int argc, char** argv){
	if(argc!=3){
		std::cerr<<"usage: Softboard ip port\n";
		return EXIT_FAILURE;
	}
	int port;
	{
		std::stringstream ss;
		ss<<argv[2];
		ss>>port;
	}
	if(!dyadInit(std::string(argv[1]), port)) return EXIT_FAILURE;
	sf::Font font;
	if(!font.loadFromMemory(courierCode, courierCodeSize)) return EXIT_FAILURE;
	Softboard softboard;
	std::stringstream ss;
	ss<<"dlal softboard "<<port;
	sf::RenderWindow window(sf::VideoMode(200, 20), ss.str().c_str());
	window.setKeyRepeatEnabled(false);
	std::set<std::string> keys;
	int result=EXIT_SUCCESS;
	while(window.isOpen()){
		if(!dyadCheck()) window.close();
		sf::Event event;
		while(window.pollEvent(event)){
			switch(event.type){
				case sf::Event::KeyPressed:
				case sf::Event::KeyReleased:{
					std::string s, t;
					t=softboard.processKey(
						event.key.code,
						event.type==sf::Event::KeyPressed,
						s
					);
					if(!t.size()) break;
					if(!dyadWrite(t)){
						result=EXIT_FAILURE;
						window.close();
					}
					if(event.type==sf::Event::KeyPressed) keys.insert(s);
					else keys.erase(s);
					break;
				}
				case sf::Event::Closed:
					window.close();
					break;
				default: break;
			}
		}
		window.clear();
		std::string s;
		for(auto i: keys) s+=i;
		sf::Text t(s.c_str(), font, 16);
		t.setPosition(2, 2);
		window.draw(t);
		window.display();
		std::this_thread::sleep_for(std::chrono::milliseconds(1));
	}
	if(!dyadFinish()) return EXIT_FAILURE;
	return result;
}
