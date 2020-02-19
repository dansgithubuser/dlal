#ifndef DLAL_FILEI_INCLUDED
#define DLAL_FILEI_INCLUDED

#include <skeleton.hpp>
#include <page.hpp>

#include <thread>

namespace dlal{

class Filei: public MultiOut, SamplesPerEvaluationGetter{
	public:
		Filei();
		~Filei();
		std::string type() const override { return "filei"; }
		void evaluate() override;
	private:
		uint64_t _evaluation;
		std::vector<Page> _loaded;
		unsigned _index;
		std::string _fileName;
		std::ifstream _file;
		Queue<Page> _queue;
		std::thread _thread;
		bool _quit=false;
};

}//namespace dlal

#endif
