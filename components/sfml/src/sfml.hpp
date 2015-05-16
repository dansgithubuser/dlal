#ifndef DLAL_SFML_INCLUDED
#define DLAL_SFML_INCLUDED

#include <skeleton.hpp>
#include <queue.hpp>

#include <SFML/Graphics.hpp>

#include <thread>
#include <atomic>

namespace dlal{

class Sfml: public Component{
	public:
		Sfml();
		~Sfml();
		void evaluate(unsigned samples);
		MidiMessages* readMidi();
	private:
		void processKey(bool on, sf::Keyboard::Key key);
		int _octave;
		Queue<MidiMessage> _queue;
		MidiMessages _messages;
		std::thread _thread;
		std::atomic<bool> _quit;
};

}//namespace dlal

#endif
