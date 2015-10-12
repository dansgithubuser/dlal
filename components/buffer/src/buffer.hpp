#ifndef DLAL_BUFFER_INCLUDED
#define DLAL_BUFFER_INCLUDED

#include <skeleton.hpp>

namespace dlal{

class Buffer: public MultiOut, public Periodic{
	public:
		Buffer();
		std::string type() const { return "buffer"; }
		void evaluate();
		float* audio();
		bool hasAudio(){ return true; }
		void resize();
	private:
		std::vector<float> _audio;
		bool _clearOnEvaluate;
};

}//namespace dlal

#endif
