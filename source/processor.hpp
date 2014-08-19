#ifndef DLAL_PROCESSOR_INCLUDED
#define DLAL_PROCESSOR_INCLUDED

#include "fm.hpp"
#include "queue.hpp"

#include <string>
#include <vector>
#include <map>
#include <iostream>

namespace dlal{

class Processor{
	public:
		struct Object{
			enum Type{ SONIC };
			Type type;
			Sonic sonic;
		};
		Processor(unsigned sampleRate, unsigned size, std::ostream& errorStream);
		void addObject(const std::string& name, Object, int channel);
		void processText(const std::string&);
		void processMidi(const std::vector<unsigned char>& midi);
		void processMic(const float* samples);
		void output(float*);
	private:
		struct Op{
			enum Type{ MIDI, MIC, ACTIVATE };
			Type type;
			std::vector<unsigned char> midi;//MIDI
			std::vector<float> mic;//MIC
			Object* object;//ACTIVATE
			unsigned channel;//ACTIVATE
		};
		void processOp(const Op&);
		std::ostream& _errorStream;
		const unsigned _sampleRate;
		std::vector<float> _samples;
		dlal::Queue<Op> _queue;
		std::map<std::string, Object> _objects;
		std::map<int, Object*> _channelToObject;
};

}//namespace dlal

#endif
