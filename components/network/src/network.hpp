#ifndef DLAL_NETWORK_INCLUDED
#define DLAL_NETWORK_INCLUDED

#include <skeleton.hpp>
#include <page.hpp>
#include <queue.hpp>

#include <vector>
#include <thread>
#include <mutex>

namespace dlal{

class Network: public Component{
	public:
		Network();
		~Network();
		void evaluate(unsigned samples);
		float* readAudio();
		MidiMessages* readMidi();
		std::string* readText();
		void queue(const Page&);
	private:
		Queue<Page> _queue;
		std::vector<float> _audio;
		MidiMessages _midi;
		std::string _text;
		bool _inited, _quit;
		std::thread _thread;
		std::mutex _mutex;
};

}//namespace dlal

#endif
