#ifndef DLAL_BUFFER_INCLUDED
#define DLAL_BUFFER_INCLUDED

#include <skeleton.hpp>

namespace dlal{

class Buffer: public Component{
	public:
		Buffer();
		std::string readyToEvaluate();
		void evaluate(unsigned samples);
		float* readAudio();
	private:
		std::vector<float> _audio;
		unsigned _i;
};

}//namespace dlal

#endif
