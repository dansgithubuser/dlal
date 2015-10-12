#ifndef DLAL_PAGE_INCLUDED
#define DLAL_PAGE_INCLUDED

#include "skeleton.hpp"

#include <string>
#include <vector>
#include <fstream>
#include <cstdint>

namespace dlal{

struct Page{
	Page(){}
	Page(const float* audio, unsigned size, uint64_t evaluation);
	Page(const uint8_t* midi, unsigned size, uint64_t evaluation);
	Page(const std::string& text, uint64_t evaluation);
	Page(std::istream&);
	void toFile(std::ostream&) const;
	void dispatch(
		const Component& component,
		std::vector<Component*>& outputs,
		int samplesPerEvaluation
	) const;
	enum Type{ AUDIO, MIDI, TEXT };
	Type _type;
	uint64_t _evaluation;
	std::vector<float> _audio;
	std::vector<uint8_t> _midi;
	std::string _text;
};

}//namespace dlal

#endif
