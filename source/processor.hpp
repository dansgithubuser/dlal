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
		class Rec{
			public:
				Rec();
				Rec(Rec&);
				~Rec();
				void reserve(unsigned);
				bool push_back(float);
				void clear();
				float* samples;
				unsigned size, capacity;
		};
		struct Op{
			enum Type{ MIDI, MIC, SONIC, TEMPO, LENGTH, LINE, UNLINE, BEAT, SILENCE, REC_MAKE, REC, UNREC, REC_SWITCH };
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
				Line* line;//LINE, UNLINE
				float beat;//BEAT
				Rec* rec;//REC_MAKE, REC, UNREC
			};
		};
		void processOp(const Op&);
		void processNexts();
		void allocateNextRecPair(unsigned size);
		std::ostream& _errorStream;
		const unsigned _sampleRate;
		std::vector<float> _samples;
		dlal::Queue<Op> _queue;
		//looping
		unsigned _beat;
		unsigned _samplesAfterBeat;
		unsigned _samplesPerBeat;
		unsigned _beatsPerLoop;
		unsigned _nextSamplesPerBeat;
		unsigned _nextBeatsPerLoop;
		unsigned _reqdSamplesPerBeat;
		unsigned _reqdBeatsPerLoop;
		//sonics
		std::map<std::string, Sonic> _sonics;
		std::map<int, Sonic*> _channelToSonic;
		//lines
		std::map<std::string, Line> _lines;
		std::vector<Line*> _activeLines;
		std::vector<Line*> _nextLines;
		std::vector<Line*> _removeLines;
		//rec
		unsigned _currentRec;
		unsigned _currentRecPair;
		Rec _recPairs[2][2];
		bool _switchRecPair;
		std::map<std::string, Rec> _recs;
		std::vector<Rec*> _activeRecs;
		std::vector<Rec*> _nextRecs;
		std::vector<Rec*> _removeRecs;
		unsigned _recSample;
};

}//namespace dlal

#endif
