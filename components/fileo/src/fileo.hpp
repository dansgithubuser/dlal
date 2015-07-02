#ifndef DLAL_FILEO_INCLUDED
#define DLAL_FILEO_INCLUDED

#include <skeleton.hpp>
#include <page.hpp>
#include <queue.hpp>

#include <thread>

namespace dlal{

class Fileo: public SamplesPerEvaluationGetter{
	public:
		Fileo();
		~Fileo();
		std::string command(const std::string&);
		void evaluate();
		void midi(const uint8_t* bytes, unsigned size);
		bool midiAccepted(){ return true; }
		float* audio();
		bool hasAudio(){ return true; }
	private:
		void finish();
		uint64_t _evaluation;
		Queue<Page> _queue;
		std::vector<float> _audio;
		bool _audioRead;
		std::ofstream _file;
		std::thread _thread;
		bool _quit;
};

}//namespace dlal

#endif
