#ifndef DLAL_FILEI_INCLUDED
#define DLAL_FILEI_INCLUDED

#include <skeleton.hpp>
#include <page.hpp>

namespace dlal{

class Filei: public Component{
	public:
		Filei();
		std::string readyToEvaluate();
		void evaluate(unsigned samples);
		float* readAudio();
		MidiMessages* readMidi();
		std::string* readText();
	private:
		void reset();
		uint64_t _evaluation;
		std::vector<Page> _loaded;
		unsigned _index;
		float* _audio;
		std::vector<float> _emptyAudio;
		MidiMessages* _midi;
		MidiMessages _emptyMidi;
		std::string* _text;
		std::string _emptyText;
};

}//namespace dlal

#endif
