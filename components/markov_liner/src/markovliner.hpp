#ifndef DLAL_MARKOV_LINER_INCLUDED
#define DLAL_MARKOV_LINER_INCLUDED

#include <skeleton.hpp>

#include <random>

namespace dlal{

class MarkovLiner: public MultiOut, public Periodic, public SampleRateGetter {
	public:
		using Midi=std::vector<uint8_t>;

		struct State {
			std::string str() const;
			void dstr(std::stringstream& ss);
			Midi on, off;
			uint64_t duration;
		};

		struct Transition {
			std::string str() const;
			void dstr(std::stringstream& ss);
			float weight;
			size_t state;
		};

		MarkovLiner();
		std::string type() const override { return "markov_liner"; }
		void evaluate() override;
	private:
		enum MainState{ WAITING, PLAYING, DONE };
		void becomeState(size_t state);
		size_t selectState();
		std::vector<State> _states;
		std::map<size_t, std::vector<Transition>> _transitions;
		MainState _mainState=WAITING;
		size_t _state=0;
		uint64_t _stateAge=0;
		std::minstd_rand0 _rng;
};

}//namespace dlal

#endif
