#include "viewer.hpp"

#include <dryad.hpp>

#include <sstream>
#include <iostream>

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
					default: break;
				}
			}
			window->clear();
		}
		//process viewer
		std::string s;
		while(client.readSizedString(s)) viewer.process(s);
		viewer.render(wv, wt);
		//display
		for(auto window: windows) window->display();
		//don't spin
		std::this_thread::sleep_for(std::chrono::milliseconds(1));
	}
	//cleanup
	for(auto window: windows) window->close();
	return EXIT_SUCCESS;
}
