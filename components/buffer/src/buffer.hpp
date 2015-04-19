#ifndef DLAL_BUFFER_INCLUDED
#define DLAL_BUFFER_INCLUDED

#include <skeleton.hpp>

namespace dlal{

class Buffer: public Component{
	public:
		Buffer();
		bool ready();
		void evaluate(unsigned samples);
		float* readAudio();
		std::string* readText();
	private:
		std::vector<float> _audio;
		unsigned _i;
		std::string _text;
};

}//namespace dlal

#endif
