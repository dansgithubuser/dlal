#ifndef DLAL_COMMANDER_INCLUDED
#define DLAL_COMMANDER_INCLUDED

#include <skeleton.hpp>
#include <queue.hpp>

#include <atomic>
#include <vector>

namespace dlal{

class Commander: public Component{
	public:
		Commander();
		std::string addOutput(Component*);
		std::string readyToEvaluate();
		void evaluate(unsigned samples);
	private:
		Queue<std::string> _queue;
		std::vector<Component*> _outputs;
		unsigned _period, _phase;
};

}//namespace dlal

#endif
