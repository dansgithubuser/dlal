#ifndef DLAL_LINER_INCLUDED
#define DLAL_LINER_INCLUDED

#include <skeleton.hpp>

#include <atomiclist.hpp>
#include <midi.hpp>

#include <iostream>
#include <set>
#include <array>

namespace dlal{

class Liner: public MultiOut, public Periodic, public SampleRateGetter{
	public:
		struct Midi{
			Midi(){}
			Midi(uint64_t sample, std::vector<uint8_t> midi): sample(sample), midi(midi) {}
			Midi(uint64_t sample, float sampleRemainder, std::vector<uint8_t> midi): sample(sample), sampleRemainder(sampleRemainder), midi(midi) {}
			uint64_t sample;
			float sampleRemainder=0.0f;
			std::vector<uint8_t> midi;
		};
		Liner();
		std::string type() const { return "liner"; }
		void evaluate();
		void midi(const uint8_t* bytes, unsigned size);
		bool midiAccepted(){ return true; }
		std::string setPhase(uint64_t);
	private:
		struct Gene{
			bool operator==(const Gene& other) const { return notes==other.notes; }
			std::vector<Midi> midi;
			std::set<uint8_t> notes;
		};
		void advance(uint64_t phase);
		void put(const uint8_t* midi, unsigned size, uint64_t sample);
		dlal::Midi getMidi() const;
		std::string putMidi(dlal::Midi, float samplesPerQuarter, unsigned track=1);
		void resetGene0();
		AtomicList<Midi> _line;
		AtomicList<Midi>::Iterator _iterator;
		float _samplesPerQuarter=22050.0f;
		bool _resetOnMidi=false, _loopOnRepeat=false;
		std::array<std::vector<Gene>, 2> _genes;
		int _notesPlaying=0;
};

}//namespace dlal

std::ostream& operator<<(std::ostream& o, const dlal::Liner::Midi& midi);

#endif
