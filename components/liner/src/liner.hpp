#ifndef DLAL_LINER_INCLUDED
#define DLAL_LINER_INCLUDED

#include <skeleton.hpp>

#include <midi.hpp>

#include <iostream>
#include <set>
#include <sstream>
#include <array>

namespace dlal{

class Liner: public MultiOut, public Periodic, public SampleRateGetter{
	public:
		struct Midi{
			Midi(){}
			Midi(uint64_t sample, std::vector<uint8_t> midi): sample(sample), midi(midi) {}
			Midi(uint64_t sample, float sampleRemainder, std::vector<uint8_t> midi): sample(sample), sampleRemainder(sampleRemainder), midi(midi) {}
			std::string str() const;
			int64_t sample;
			float sampleRemainder=0.0f;
			std::vector<uint8_t> midi;
		};
		Liner();
		std::string type() const override { return "liner"; }
		void evaluate() override;
		void midi(const uint8_t* bytes, unsigned size) override;
		bool midiAccepted() override { return true; }
		std::string setPhase(uint64_t) override;
	private:
		static const int NOTE_SENTINEL=0xff;
		void advance(uint64_t phase);
		void process(const uint8_t* midi, unsigned size, uint64_t sample);
		void put(Midi midi);
		dans::Midi getMidi() const;
		std::string putMidi(dans::Midi, unsigned track=1);
		std::set<uint8_t> grabGene(std::vector<Midi>::iterator& i, std::vector<Midi>::iterator end) const;
		int64_t noteEnd(std::vector<Midi>::iterator i, std::vector<Midi>::iterator end) const;
		std::vector<Midi> _line;
		size_t _index;
		float _samplesPerQuarter=22050.0f;
		bool _resetOnMidi=false, _transplantOnMidi=false, _loopOnRepeat=false;
		uint8_t _transplantNote=NOTE_SENTINEL;
		std::set<uint8_t> _allNotes;
		uint8_t _minNote;
		std::array<std::vector<Midi>, 2> _genes;
		float _fudge=0.1f;
};

}//namespace dlal

#endif
