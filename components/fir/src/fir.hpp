#ifndef DLAL_FIR_INCLUDED
#define DLAL_FIR_INCLUDED

#include <skeleton.hpp>
#include <ringbuffer.hpp>

#include <complex>

namespace dlal{

class Fir: public SamplesPerEvaluationGetter, public SampleRateGetter, public MultiOut {
	public:
		Fir();
		std::string connect(Component& output);
		std::string disconnect(Component& output);
		std::string type() const { return "fir"; }
		void evaluate();
	private:
		struct Formant{
			Formant();
			Formant(float frequency, float magnitude, float width, float speed);
			void toward(const Formant&);
			void apply(std::vector<double>&, unsigned sampleRate);
			float _frequency, _magnitude, _width, _speed;
		};
		void resize(unsigned);
		std::vector<double> _ir;
		std::vector<std::pair<Component*, Ringbuffer<float>>> _x;
		std::vector<std::pair<Formant, Formant>> _formants;
};

}//namespace dlal

#endif
