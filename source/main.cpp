#include "audio.hpp"

#include <iostream>
#include <string>

int main(int argc, char** argv){
	dlal::init();
	std::cout<<"started\n";
	std::string s;
	std::cin>>s;
	dlal::finish();
	return 0;
}
