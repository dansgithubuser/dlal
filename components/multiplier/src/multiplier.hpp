#ifndef DLAL_MULTIPLIER_INCLUDED
#define DLAL_MULTIPLIER_INCLUDED

#include <skeleton.hpp>

namespace dlal{

class Multiplier: public Component{
	public:
		Multiplier();
		std::string addOutput(Component*);
		std::string readyToEvaluate();
		void evaluate(unsigned samples);
	private:
		Component* _input;
		Component* _output;
		float _multiplier;
};

}//namespace dlal

#endif
