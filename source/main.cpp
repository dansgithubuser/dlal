#include "audio.hpp"
#include "midi.hpp"
#include "fm.hpp"
#include "processor.hpp"

#include <SFML/Graphics.hpp>

#include <iostream>
#include <string>
#include <thread>

const unsigned LOG2_SAMPLES_PER_CALLBACK=6;
const unsigned SAMPLES_PER_CALLBACK=1<<LOG2_SAMPLES_PER_CALLBACK;
const unsigned SAMPLE_RATE=44100;

void printHelp(){
	std::cout<<"Enter Help to print this text."<<std::endl;
	std::cout<<"Enter Quit to quit."<<std::endl;
	std::cout<<std::endl;
}

int main(int argc, char** argv){
	sf::RenderWindow window(sf::VideoMode(320, 240, 32), "dlal display");
	dlal::Processor processor(SAMPLE_RATE, SAMPLES_PER_CALLBACK, std::cout);
	dlal::audioInit(
		[&](const float* input, float* output){
			processor.processMic(input);
			processor.output(output);
		},
		SAMPLE_RATE,
		LOG2_SAMPLES_PER_CALLBACK
	);
	dlal::midiInit([&](std::vector<unsigned char>& message){
		processor.processMidi(message);
	});
	printHelp();
	bool done=false;
	std::thread inputThread([&](){
		while(true){
			std::string s;
			std::cout<<">";
			std::getline(std::cin, s);
			if(s=="Quit") break;
			else if(s=="Help") printHelp();
			else processor.processText(s);
		}
		done=true;
	});
	while(!done){
		sf::Color c;
		unsigned beat=processor.beat();
		if(beat){
			c.r=255;
			if((beat-1)%2==0) c.g=255;
			if((beat-1)%4==0) c.b=255;
		}
		sf::RectangleShape rect(sf::Vector2f(100.0f, 100.0f));
		rect.setPosition(0.0f, 0.0f);
		rect.setFillColor(c);
		window.draw(rect);
		window.display();
		sf::sleep(sf::seconds(1/60.0f));
		sf::Event sfEvent;
		while(window.pollEvent(sfEvent));
	}
	inputThread.join();
	dlal::midiFinish();
	dlal::audioFinish();
	return 0;
}
