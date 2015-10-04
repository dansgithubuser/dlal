#include "viewer.hpp"

#include <queue.hpp>

#include <dyad.h>

#include <sstream>
#include <thread>
#include <chrono>
#include <cstdlib>
#include <cassert>
#include <iostream>
#include <atomic>

static std::atomic<bool> fQuit=false;
static dlal::Queue<std::string> fQueue(8);

static void atPanic(const char* message){
	assert(0);
	exit(1);
}

static void atDestroy(dyad_Event* e){ if(!fQuit) exit(0); }

static void atError(dyad_Event* e){
	std::cerr<<"dyad error: "<<e->msg<<"\n";
	assert(0);
	exit(1);
}

static void atData(dyad_Event* e){
	fQueue.write(std::string(e->data));
}

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
	dyad_atPanic(atPanic);
	dyad_init();
	dyad_Stream* stream=dyad_newStream();
	dyad_addListener(stream, DYAD_EVENT_DESTROY, atDestroy, NULL);
	dyad_addListener(stream, DYAD_EVENT_ERROR  , atError  , NULL);
	dyad_addListener(stream, DYAD_EVENT_DATA   , atData   , NULL);
	dyad_connect(stream, argv[1], port);
	auto thread=std::thread([](){ while(!fQuit) dyad_update(); });
	//sfml
	sf::RenderWindow wv(sf::RenderWindow(sf::VideoMode(640, 480), "dlal viewer - system visualization"));
	sf::RenderWindow wt(sf::RenderWindow(sf::VideoMode(240, 480), "dlal viewer - text"));
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
		while(fQueue.read(s, true)) viewer.process(s);
		viewer.render(wv, wt);
		//display
		for(auto window: windows) window->display();
		//don't spin
		std::this_thread::sleep_for(std::chrono::milliseconds(1));
	}
	for(auto window: windows) window->close();
	//cleanup
	fQuit=true;
	thread.join();
	dyad_shutdown();
	return EXIT_SUCCESS;
}
