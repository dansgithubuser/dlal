#ifndef DLAL_MULTIPLIER_INCLUDED
#define DLAL_MULTIPLIER_INCLUDED

#include <skeleton.hpp>

namespace dlal{

class Multiplier: public Component{
	public:
		Multiplier();
		bool ready();
		void addOutput(Component*);
		void evaluate(unsigned samples);
		std::string* readText();
		void clearText();
		bool sendText(const std::string&);
    std::string commands();
	private:
		Component* _input;
		Component* _output;
		float _multiplier;
		std::string _text;
};

}//namespace dlal

#endif
