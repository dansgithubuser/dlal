#ifndef DLAL_FILEO_INCLUDED
#define DLAL_FILEO_INCLUDED

#include <skeleton.hpp>
#include <page.hpp>

#include <thread>

namespace dlal{

class Fileo: public SamplesPerEvaluationGetter{
	public:
		Fileo();
		~Fileo();
		std::string type() const override { return "fileo"; }
		std::string command(const std::string&) override;
		void evaluate() override;
		void midi(const uint8_t* bytes, unsigned size) override;
		bool midiAccepted() override { return true; }
		float* audio() override;
		bool hasAudio() override { return true; }
	private:
		void finish();
		uint64_t _evaluation;
		Queue<Page> _queue;
		std::vector<float> _audio;
		bool _audioRead;
		std::ofstream _file;
		std::thread _thread;
		bool _quit;
};

}//namespace dlal

#endif
