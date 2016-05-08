#include <page.hpp>

#include <dryad.hpp>
#include <courierCode.hpp>

#include <SFML/Graphics.hpp>

#include <iostream>
#include <cstdlib>
#include <sstream>
#include <thread>
#include <chrono>
#include <set>

std::string processKey(sf::Keyboard::Key key, bool on, std::string& s){
	if(key<0||key>=sf::Keyboard::Key::KeyCount) return "";
	std::string names[]={
		"a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
		"n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
		"0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
		"Esc",
		"LCtrl", "LShift", "LAlt", "LSys",
		"RCtrl", "RShift", "RAlt", "RSys",
		"Menu",
		"[", "]", ";", ",", ".", "'", "/", "\\", "`", "=", "-",
		"Space", "Return", "Backspace", "Tab",
		"PageUp", "PageDown", "End", "Home", "Insert", "Delete",
		"N+", "N-", "N*", "N/",
		"Left", "Right", "Up", "Down",
		"N0", "N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8", "N9",
		"F1" , "F2" , "F3" , "F4" , "F5" ,
		"F6" , "F7" , "F8" , "F9" , "F10",
		"F11", "F12", "F13", "F14", "F15",
		"Pause",
	};
	s=names[key];
	std::stringstream ss;
	dlal::Page(s+std::string(on?" 1":" 0"), 0).toFile(ss);
	return ss.str();
}

int main(int argc, char** argv){
	if(argc<3||argc>4){
		std::cerr<<"usage: Softboard ip port [key]\n";
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
	//command-line
	if(argc>3){
		std::stringstream ss;
		dlal::Page(argv[3], 0).toFile(ss);
		client.writeSizedString(ss.str());
		return EXIT_SUCCESS;
	}
	//sfml
	sf::Font font;
	if(!font.loadFromMemory(courierCode, courierCodeSize)) return EXIT_FAILURE;
	std::stringstream ss;
	ss<<"dlal softboard "<<port;
	sf::RenderWindow window(sf::VideoMode(200, 20), ss.str().c_str());
	window.setKeyRepeatEnabled(false);
	//loop
	std::set<std::string> keys;
	auto lastDraw=std::chrono::steady_clock::now();
	while(window.isOpen()){
		sf::Event event;
		while(window.pollEvent(event)){
			switch(event.type){
				case sf::Event::KeyPressed:
				case sf::Event::KeyReleased:{
					std::string s, t;
					t=processKey(
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
	return EXIT_SUCCESS;
}
