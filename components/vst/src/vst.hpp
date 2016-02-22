#ifndef DLAL_VST_INCLUDED
#define DLAL_VST_INCLUDED

#include <skeleton.hpp>

#include <atomic>
#include <functional>

namespace dlal{

class Vst: public SamplesPerEvaluationGetter, public SampleRateGetter, public MultiOut {
	public:
		Vst();
		~Vst();
		std::string type() const { return "vst"; }
		void evaluate();
		void midi(const uint8_t* bytes, unsigned size);
		bool midiAccepted(){ return true; }
	private:
		struct Plugin{
			typedef int* (*Dispatcher)(Plugin*, int32_t, int32_t, int*, void*, float);
			typedef void (*Process)(Plugin*, float**, float**, int32_t);
			typedef void (*SetParameter)(Plugin*, int32_t, float);
			typedef float (*GetParameter)(Plugin*, int32_t);
			int32_t magic;
			Dispatcher dispatcher;
			Process processDeprecated;
			SetParameter setParameter;
			GetParameter getParameter;
			int32_t programs, params, inputs, outputs, flags, reserved1, reserved2, initialDelay, realQualitiesDeprecated, offQualitiesDeprecated;
			float ioRatioDeprecated;
			void* object;
			void* user;
			int32_t id, version;
			Process processReplacing;
		};
		typedef int* (Vst2xHostCallback)(Plugin* effect, int32_t opcode, int32_t index, int* value, void* data, float opt);
		static Vst2xHostCallback vst2xHostCallback;
		static Vst* _self;
		static std::atomic<bool> _hostCallbackExpected;
		std::string operateOnPlugin(std::function<std::string()>);
		Plugin* _plugin;
		std::vector<float> _i;
		uint64_t _samples;
		double _samplesPerBeat, _startToNowInQuarters, _lastBarToNowInQuarters;
		int32_t _beatsPerBar, _beatsPerQuarter;
};

}//namespace dlal

#endif
