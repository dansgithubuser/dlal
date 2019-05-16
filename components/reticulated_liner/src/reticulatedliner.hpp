#ifndef DLAL_RETICULATED_LINER_INCLUDED
#define DLAL_RETICULATED_LINER_INCLUDED

#include <skeleton.hpp>

#include <midi.hpp>

#include <iostream>

namespace dlal{

class ReticulatedLiner: public MultiOut {
	public:
		ReticulatedLiner();
		std::string type() const override { return "reticulated_liner"; }
		void midi(const uint8_t* bytes, unsigned size) override;
		bool midiAccepted() override { return true; }
	private:
		dans::Midi getMidi() const;
		std::string putMidi(dans::Midi);
		using Reticule=std::vector<std::vector<uint8_t>>;
		std::vector<Reticule> _line;
		size_t _index;
		uint8_t _playing=0xff;
};

}//namespace dlal

#endif
