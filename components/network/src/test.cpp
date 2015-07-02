#include "network.hpp"

#include <iostream>
#include <cstdlib>
#include <thread>
#include <chrono>
#include <string>

int main(int argc, char** argv){
	if(argc!=2){
		std::cerr<<"usage: Network port\n";
		return EXIT_FAILURE;
	}
	dlal::Network network;
	network.command("open "+std::string(argv[1]));
	bool quit=false;
	std::thread thread([&](){
		while(!quit){
			network.evaluate();
			std::this_thread::sleep_for(std::chrono::milliseconds(1));
		}
	});
	std::string s;
	std::cin>>s;
	quit=true;
	thread.join();
	return EXIT_SUCCESS;
}
