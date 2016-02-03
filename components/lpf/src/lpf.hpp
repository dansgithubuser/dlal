#ifndef DLAL_LPF_INCLUDED
#define DLAL_LPF_INCLUDED

#include <skeleton.hpp>

namespace dlal{

class Lpf: public MultiOut, public SamplesPerEvaluationGetter{
	public:
		Lpf();
		std::string type() const { return "lpf"; }
		void evaluate();
		void midi(const uint8_t* bytes, unsigned size);
		bool midiAccepted(){ return true; }
	private:
		static const int PITCH_WHEEL_PRETEND_CONTROL=0x100;
		float _lowness;
		struct Float{
			Float(): _(0.0f) {}
			float _;
		};
		std::map<Component*, Float> _y;
		int _control, _min, _max;
		bool _listening;
		class Range{
			public:
				Range(): _new(true) {}
				operator int(){ return _max-_min; }
				void value(int v){
					if(_new){
						_min=_max=v;
						_new=false;
						return;
					}
					if     (v<_min) _min=v;
					else if(v>_max) _max=v;
				}
				int _min, _max;
			private:
				bool _new;
		};
		std::map<int, Range> _listeningControls;
		std::vector<float> _f;
};

}//namespace dlal

#endif
