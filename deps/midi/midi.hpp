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
				Event(){}
				Event(int ticks): ticks(ticks) {}
				Event(int ticks, const std::vector<uint8_t>& data);

				bool operator<(const Event& other) const { return ticks<other.ticks; }

				Event& setTempo(int _){ type=TEMPO; usPerQuarter=_; return *this; }
				Event& setTimeSig(uint8_t t, uint8_t b){ type=TIME_SIG; timeSigTop=t; timeSigBottom=b; return *this; }
				Event& setKeySig(int s, bool m){ type=KEY_SIG; sharps=s; minor=m; return *this; }
				Event& setNote(int d, uint8_t n, uint8_t vd, uint8_t vu){ type=NOTE; duration=d; note=n; velocityDown=vd; velocityUp=vu; return *this; }

				void write(std::vector<uint8_t>&) const;
				int end() const;

				enum Type{
					TEMPO,
					TIME_SIG,
					KEY_SIG,
					NOTE, NOTE_ON, NOTE_OFF,
					SENTINEL,
				};

				Type type=SENTINEL;
				int ticks;
				uint8_t channel=0;
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
		struct Pair{ int delta; std::vector<uint8_t> event; };
		typedef std::vector<Event> Track;

		Midi(): ticksPerQuarter(256) {}

		void append(unsigned track, int delta, const Event& event);
		void append(unsigned track, int delta, const std::vector<uint8_t>& data);

		void read(std::string filename);
		void write(std::string filename) const;
		void read(const std::vector<uint8_t>&);
		void write(std::vector<uint8_t>&) const;

		int duration() const;

		int ticksPerQuarter;
		std::vector<Track> tracks;
};

void splitNotes(Midi::Track&);
std::vector<Midi::Pair> getPairs(Midi::Track);

}//namespace dlal

std::ostream& operator<<(std::ostream& o, const dlal::Midi::Event& event);
std::ostream& operator<<(std::ostream& o, const dlal::Midi::Pair& pair);

#endif
