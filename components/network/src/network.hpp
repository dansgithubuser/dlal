#ifndef DLAL_NETWORK_INCLUDED
#define DLAL_NETWORK_INCLUDED

#include <skeleton.hpp>
#include <page.hpp>
#include <queue.hpp>

#include <vector>
#include <thread>
#include <mutex>

namespace dlal{

class Network: public MultiOut, public SamplesPerEvaluationGetter{
	public:
		Network();
		~Network();
		void evaluate();
		void queue(const Page&);
	private:
		Queue<Page> _queue;
		bool _inited, _quit;
		std::thread _thread;
		std::mutex _mutex;
};

}//namespace dlal

#endif
