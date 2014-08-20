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
		Processor(unsigned sampleRate, unsigned size, std::ostream& errorStream);
		void addSonic(const std::string& name, Sonic, int channel);
		void processText(const std::string&);
		void processMidi(const std::vector<unsigned char>& midi);
		void processMic(const float* samples);
		void output(float*);
	private:
		struct Line{
			Line();
			struct Event{
				float beat;
				std::vector<unsigned char> message;
			};
			std::vector<Event> events;
			unsigned i;
		};
		struct Op{
			enum Type{ MIDI, MIC, SONIC, TEMPO, LENGTH, LINE };
			Type type;
			std::vector<unsigned char> midi;//MIDI
			std::vector<float> mic;//MIC
			union{
				struct{
					Sonic* sonic;//SONIC
					unsigned channel;//SONIC
				};
				unsigned samplesPerBeat;//TEMPO
				unsigned beatsPerLoop;//LENGTH
				Line* line;//LINE
			};
		};
		void processOp(const Op&);
		std::ostream& _errorStream;
		const unsigned _sampleRate;
		std::vector<float> _samples;
		dlal::Queue<Op> _queue;
		unsigned _beat;
		unsigned _samplesAfterBeat;
		unsigned _samplesPerBeat;
		unsigned _beatsPerLoop;
		unsigned _nextSamplesPerBeat;
		unsigned _nextBeatsPerLoop;
		std::map<std::string, Sonic> _sonics;
		std::map<int, Sonic*> _channelToSonic;
		std::map<std::string, Line> _lines;
		std::vector<Line*> _activeLines;
		std::vector<Line*> _nextLines;
};

}//namespace dlal

#endif
