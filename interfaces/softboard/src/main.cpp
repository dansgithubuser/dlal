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
	switch(key){
		case sf::Keyboard::Key::Comma    : s=","       ; break;
		case sf::Keyboard::Key::Period   : s="."       ; break;
		case sf::Keyboard::Key::SemiColon: s=";"       ; break;
		case sf::Keyboard::Key::Slash    : s="/"       ; break;
		case sf::Keyboard::Key::BackSlash: s="\\"      ; break;
		case sf::Keyboard::Key::LBracket : s="["       ; break;
		case sf::Keyboard::Key::RBracket : s="]"       ; break;
		case sf::Keyboard::Key::Equal    : s="="       ; break;
		case sf::Keyboard::Key::Dash     : s="-"       ; break;
		case sf::Keyboard::Key::Up       : s="Up"      ; break;
		case sf::Keyboard::Key::Down     : s="Down"    ; break;
		case sf::Keyboard::Key::Space    : s="Space"   ; break;
		case sf::Keyboard::Key::Return   : s="Return"  ; break;
		case sf::Keyboard::Key::PageUp   : s="PageUp"  ; break;
		case sf::Keyboard::Key::PageDown : s="PageDown"; break;
		case sf::Keyboard::Key::F1       : s="F1"      ; break;
		case sf::Keyboard::Key::F2       : s="F2"      ; break;
		case sf::Keyboard::Key::F3       : s="F3"      ; break;
		case sf::Keyboard::Key::F4       : s="F4"      ; break;
		case sf::Keyboard::Key::F5       : s="F5"      ; break;
		case sf::Keyboard::Key::F6       : s="F6"      ; break;
		case sf::Keyboard::Key::F7       : s="F7"      ; break;
		case sf::Keyboard::Key::F8       : s="F8"      ; break;
		case sf::Keyboard::Key::F9       : s="F9"      ; break;
		case sf::Keyboard::Key::F10      : s="F10"     ; break;
		case sf::Keyboard::Key::F11      : s="F11"     ; break;
		case sf::Keyboard::Key::F12      : s="F12"     ; break;
		case sf::Keyboard::Key::Num0     : s="0"       ; break;
		case sf::Keyboard::Key::Num1     : s="1"       ; break;
		case sf::Keyboard::Key::Num2     : s="2"       ; break;
		case sf::Keyboard::Key::Num3     : s="3"       ; break;
		case sf::Keyboard::Key::Num4     : s="4"       ; break;
		case sf::Keyboard::Key::Num5     : s="5"       ; break;
		case sf::Keyboard::Key::Num6     : s="6"       ; break;
		case sf::Keyboard::Key::Num7     : s="7"       ; break;
		case sf::Keyboard::Key::Num8     : s="8"       ; break;
		case sf::Keyboard::Key::Num9     : s="9"       ; break;
		case sf::Keyboard::Key::A        : s="A"       ; break;
		case sf::Keyboard::Key::B        : s="B"       ; break;
		case sf::Keyboard::Key::C        : s="C"       ; break;
		case sf::Keyboard::Key::D        : s="D"       ; break;
		case sf::Keyboard::Key::E        : s="E"       ; break;
		case sf::Keyboard::Key::F        : s="F"       ; break;
		case sf::Keyboard::Key::G        : s="G"       ; break;
		case sf::Keyboard::Key::H        : s="H"       ; break;
		case sf::Keyboard::Key::I        : s="I"       ; break;
		case sf::Keyboard::Key::J        : s="J"       ; break;
		case sf::Keyboard::Key::K        : s="K"       ; break;
		case sf::Keyboard::Key::L        : s="L"       ; break;
		case sf::Keyboard::Key::M        : s="M"       ; break;
		case sf::Keyboard::Key::N        : s="N"       ; break;
		case sf::Keyboard::Key::O        : s="O"       ; break;
		case sf::Keyboard::Key::P        : s="P"       ; break;
		case sf::Keyboard::Key::Q        : s="Q"       ; break;
		case sf::Keyboard::Key::R        : s="R"       ; break;
		case sf::Keyboard::Key::S        : s="S"       ; break;
		case sf::Keyboard::Key::T        : s="T"       ; break;
		case sf::Keyboard::Key::U        : s="U"       ; break;
		case sf::Keyboard::Key::V        : s="V"       ; break;
		case sf::Keyboard::Key::W        : s="W"       ; break;
		case sf::Keyboard::Key::X        : s="X"       ; break;
		case sf::Keyboard::Key::Y        : s="Y"       ; break;
		case sf::Keyboard::Key::Z        : s="Z"       ; break;
		default: return "";
	}
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
