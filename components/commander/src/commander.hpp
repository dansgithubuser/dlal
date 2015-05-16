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
		struct DequeuedCommand{
			DequeuedCommand();
			void fromString(std::string);
			unsigned _periodEdgesToWait;
			unsigned _output;
			std::string _text;
		};
		void dispatch(const DequeuedCommand&);
		Queue<std::string> _queue;
		std::vector<DequeuedCommand> _dequeued;
		unsigned _size;
		std::vector<Component*> _outputs;
		unsigned _period, _phase;
};

}//namespace dlal

#endif
