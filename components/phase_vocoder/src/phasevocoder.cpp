#include "phasevocoder.hpp"

DLAL_BUILD_COMPONENT_DEFINITION(PhaseVocoder)

extern "C" {
	void hello();
}

namespace dlal{

PhaseVocoder::PhaseVocoder(){
}

PhaseVocoder::~PhaseVocoder(){
}

void PhaseVocoder::evaluate(){
	hello();
}

}//namespace dlal
