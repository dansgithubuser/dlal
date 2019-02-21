#ifndef DLAL_NETWORK_INCLUDED
#define DLAL_NETWORK_INCLUDED

#include <skeleton.hpp>
#include <page.hpp>

#include <map>

namespace dlal{

class Network: public MultiOut, public SamplesPerEvaluationGetter{
	public:
		Network();
		std::string type() const override { return "network"; }
		void evaluate() override;
		void queue(const Page&);
		Queue<uint8_t> _data;
		Queue<Page> _forward_queue;
	private:
		int _port;
		Queue<Page> _queue;
		std::map<std::string, dlal::Page> _map;
};

}//namespace dlal

#endif
