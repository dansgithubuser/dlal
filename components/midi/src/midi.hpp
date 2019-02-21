#ifndef DLAL_MIDI_INCLUDED
#define DLAL_MIDI_INCLUDED

#include <skeleton.hpp>

#include <RtMidi.h>

namespace dlal{

class Midi: public MultiOut{
	public:
		Midi();
		~Midi();
		std::string type() const override { return "midi"; }
		void evaluate() override;
		void rtMidi(const uint8_t* bytes, unsigned size);
		void midi(const uint8_t* bytes, unsigned size) override;
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
		void evaluateMidi(const std::vector<uint8_t>&);
		RtMidiIn* _rtMidiIn;
		Queue<std::vector<uint8_t>> _rtQueue, _cmdQueue;
		std::string _portName;
		List _blacklist, _whitelist;
};

}//namespace dlal

#endif
