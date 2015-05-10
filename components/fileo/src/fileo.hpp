#ifndef DLAL_FILEO_INCLUDED
#define DLAL_FILEO_INCLUDED

#include <skeleton.hpp>
#include <page.hpp>
#include <queue.hpp>

#include <thread>

namespace dlal{

class Fileo: public Component{
	public:
		Fileo();
		~Fileo();
		std::string addInput(Component*);
		std::string readyToEvaluate();
		void evaluate(unsigned samples);
	private:
		uint64_t _evaluation;
		Component* _input;
		Queue<Page> _queue;
		std::ofstream _file;
		std::thread _thread;
		bool _quit;
};

}//namespace dlal

#endif
