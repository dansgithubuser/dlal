#include "softboard.hpp"

#include <dryad.hpp>
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
	//dyad
	dryad::Client client(std::string(argv[1]), port);
	//sfml
	sf::Font font;
	if(!font.loadFromMemory(courierCode, courierCodeSize)) return EXIT_FAILURE;
	std::stringstream ss;
	ss<<"dlal softboard "<<port;
	sf::RenderWindow window(sf::VideoMode(200, 20), ss.str().c_str());
	window.setKeyRepeatEnabled(false);
	//loop
	Softboard softboard;
	std::set<std::string> keys;
	int result=EXIT_SUCCESS;
	auto lastDraw=std::chrono::steady_clock::now();
	while(window.isOpen()){
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
					client.writeSizedString(t);
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
		if(std::chrono::steady_clock::now()-lastDraw>std::chrono::milliseconds(15)){
			window.clear();
			std::string s;
			for(auto i: keys) s+=i;
			sf::Text t(s.c_str(), font, 16);
			t.setPosition(2, 2);
			window.draw(t);
			window.display();
			lastDraw=std::chrono::steady_clock::now();
		}
		std::this_thread::sleep_for(std::chrono::milliseconds(1));
		if(client.timesDisconnected()) break;
	}
	return result;
}
