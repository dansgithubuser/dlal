#ifndef DLAL_NETWORK_INCLUDED
#define DLAL_NETWORK_INCLUDED

#include <skeleton.hpp>
#include <page.hpp>
#include <queue.hpp>

#include <map>

namespace dlal{

class Network: public MultiOut, public SamplesPerEvaluationGetter, public SystemGetter{
	public:
		Network();
		void evaluate();
		void queue(const Page&);
	private:
		int _port;
		Queue<Page> _queue;
		std::map<std::string, dlal::Page> _map;
};

}//namespace dlal

#endif
