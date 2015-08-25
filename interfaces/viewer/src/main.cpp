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
	//sfml`
	sf::RenderWindow window(sf::VideoMode(640, 480), "dlal viewer");
	window.setKeyRepeatEnabled(false);
	//loop
	Viewer viewer;
	int result=EXIT_SUCCESS;
	while(window.isOpen()){
		sf::Event event;
		while(window.pollEvent(event)){
			switch(event.type){
				case sf::Event::Closed:
					window.close();
					break;
				default: break;
			}
		}
		std::string s;
		while(fQueue.read(s, true)) viewer.process(s);
		window.clear();
		viewer.render(window);
		window.display();
		std::this_thread::sleep_for(std::chrono::milliseconds(1));
	}
	//cleanup
	fQuit=true;
	thread.join();
	dyad_shutdown();
	return result;
}
