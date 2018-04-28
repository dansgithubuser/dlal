#ifndef DLAL_MIDI_INCLUDED
#define DLAL_MIDI_INCLUDED

#include <skeleton.hpp>

#include <RtMidi.h>

namespace dlal{

class Midi: public MultiOut{
	public:
		Midi();
		~Midi();
		std::string type() const { return "midi"; }
		void evaluate();
		void midi(const uint8_t* bytes, unsigned size);
	private:
		class List{
			public:
				std::string append(std::stringstream&);
				bool match(unsigned output, const std::vector<uint8_t>&) const;
			private:
				class MidiPattern{
					public:
						std::string populate(std::stringstream&);
						bool match(const std::vector<uint8_t>&) const;
					private:
						std::vector<std::pair<char, unsigned>> _;
				};
				std::vector<std::vector<MidiPattern>> _;
		};
		std::string allocate();
		RtMidiIn* _rtMidiIn;
		Queue<std::vector<uint8_t>> _queue;
		std::string _portName;
		List _blacklist, _whitelist;
};

}//namespace dlal

#endif
