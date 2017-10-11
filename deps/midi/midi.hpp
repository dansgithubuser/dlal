#ifndef DLAL_MIDI_HPP_INCLUDED
#define DLAL_MIDI_HPP_INCLUDED

#include <cstdint>
#include <iostream>
#include <string>
#include <vector>

namespace dlal{

class Midi{
	public:
		class Event{
			public:
				Event(): type(SENTINEL) {}
				Event(int ticks, const std::vector<uint8_t>& data);
				bool operator<(Event& other) const { return ticks<other.ticks; }
				void write(std::vector<uint8_t>&) const;
				enum Type{
					TEMPO,
					TIME_SIG,
					KEY_SIG,
					NOTE, NOTE_ON, NOTE_OFF,
					SENTINEL,
				};
				Type type;
				int ticks;
				uint8_t channel;
				union{
					int usPerQuarter;//tempo
					struct{ uint8_t timeSigTop, timeSigBottom; };//time_sig
					struct{ int sharps; bool minor; };//key_sig
					struct{//note
						int duration;
						uint8_t note, velocityDown, velocityUp;
					};
				};
		};
		typedef std::vector<Event> Track;

		Midi(): ticksPerQuarter(256) {}

		void append(unsigned track, int delta, const std::vector<uint8_t>& data);

		void read(std::string filename);
		void write(std::string filename) const;

		int ticksPerQuarter;
		std::vector<Track> tracks;
	private:
		void parse(const std::vector<uint8_t>&);
		void write(std::vector<uint8_t>&) const;
};

struct Pair{ int delta; std::vector<uint8_t> event; };

void splitNotes(Midi::Track&);
std::vector<Pair> getPairs(Midi::Track);

}//namespace dlal

std::ostream& operator<<(std::ostream& o, const dlal::Midi::Event& event);

#endif
