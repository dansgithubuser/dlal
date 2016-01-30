#include "viewer.hpp"

#include <dryad.hpp>

#include <sstream>
#include <iostream>
#include <chrono>

int main(int argc, char** argv){
	if(argc!=3){
		std::cerr<<"usage: Viewer ip port\n";
		return EXIT_FAILURE;
	}
	int port;
	std::stringstream ss;
	ss<<argv[2];
	ss>>port;
	//dyad
	dryad::Client client(argv[1], port);
	//sfml
	sf::RenderWindow wv(sf::VideoMode(640, 480), "dlal viewer - system visualization");
	sf::RenderWindow wt(sf::VideoMode(240, 480), "dlal viewer - text");
	std::vector<sf::RenderWindow*> windows;
	windows.push_back(&wv);
	windows.push_back(&wt);
	//loop
	Viewer viewer;
	auto lastDraw=std::chrono::steady_clock::now();
	while(true){
		//check if any window was closed
		bool quit=false;
		for(auto window: windows) if(!window->isOpen()) quit=true;
		if(quit) break;
		//process events and clear window
		for(auto window: windows){
			sf::Event event;
			while(window->pollEvent(event)){
				switch(event.type){
					case sf::Event::Resized:
						window->setView(sf::View(sf::FloatRect(0, 0, 1.0f*event.size.width, 1.0f*event.size.height)));
						break;
					case sf::Event::Closed:
						window->close();
						break;
					case sf::Event::KeyPressed:
						if(window==&wv) switch(event.key.code){
							case sf::Keyboard::Space:
								wt.setPosition(wv.getPosition()+sf::Vector2i(wv.getSize().x, 0));
								wt.setSize(sf::Vector2u(wt.getSize().x, wv.getSize().y));
								break;
							default: break;
						}
						break;
					default: break;
				}
			}
		}
		//process viewer
		std::string s;
		if(client.timesDisconnected()) break;
		while(client.readSizedString(s)) viewer.process(s);
		if(std::chrono::steady_clock::now()-lastDraw>std::chrono::milliseconds(15)){
			for(auto window: windows) window->clear();
			viewer.render(wv, wt);
			for(auto window: windows) window->display();
			lastDraw=std::chrono::steady_clock::now();
		}
		//don't spin
		std::this_thread::sleep_for(std::chrono::milliseconds(1));
	}
	//cleanup
	for(auto window: windows) window->close();
	return EXIT_SUCCESS;
}
