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
		bool lockless();
		void processText(const std::string&);
		void processMidi(const std::vector<unsigned char>& midi);
		void processMic(const float* samples, unsigned size, unsigned micIndex);
		void output(float*);
		unsigned beat();
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
				float& operator[](unsigned i);
				const float& operator[](unsigned i) const;
				void reserve(unsigned);
				bool push_back(float);
				void clear();
				float* samples;
				unsigned size, capacity;
		};
		class Op{
			public:
				enum Type{ MIDI, MIC, SONIC, TEMPO, LENGTH, LINE, UNLINE, BEAT, SILENCE, REC_MAKE, REC, UNREC, REC_SWITCH };
				Op();
				Op(Type);
				Op(Type, unsigned);
				Op(Type, Line*);
				Op(Type, Rec*);
				Op(Sonic*, unsigned channel);
				Op(float beat);
				Op(const std::vector<unsigned char>& midi);
				Op(const float* samples, unsigned size, unsigned micIndex);
				void set(const float* samples, unsigned size, unsigned micIndex);
				Type _type;
				unsigned char _midi[32];//MIDI
				unsigned char _midiSize;//MIDI
				std::vector<float> _mic;//MIC
				union{
					unsigned _micIndex;//MIC
					struct{
						Sonic* _sonic;//SONIC
						unsigned _channel;//SONIC
					};
					unsigned _samplesPerBeat;//TEMPO
					unsigned _beatsPerLoop;//LENGTH
					Line* _line;//LINE, UNLINE
					float _beat;//BEAT
					Rec* _rec;//REC_MAKE, REC, UNREC
				};
		};
		void processOp(const Op&);
		void processNexts();
		void allocateNextRecPair(unsigned size);
		std::ostream& _errorStream;
		const unsigned _sampleRate;
		std::vector<float> _samples;
		dlal::Queue<Op> _queue;
		//mic
		std::vector<std::vector<float>> _mic;
		//looping
		unsigned _beat;
		unsigned _samplesAfterBeat;
		unsigned _samplesPerBeat;
		unsigned _beatsPerLoop;
		unsigned _nextSamplesPerBeat;
		unsigned _nextBeatsPerLoop;
		unsigned _reqdSamplesPerBeat;
		unsigned _reqdBeatsPerLoop;
		std::atomic<unsigned> _lastBeat;
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
