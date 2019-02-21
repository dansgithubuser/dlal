#ifndef DLAL_VST_INCLUDED
#define DLAL_VST_INCLUDED

#include <skeleton.hpp>

#include <functional>
#include <map>
#include <mutex>

namespace dlal{

class Vst: public SamplesPerEvaluationGetter, public SampleRateGetter, public MultiOut {
	public:
		Vst();
		std::string type() const override { return "vst"; }
		void evaluate() override;
		void midi(const uint8_t* bytes, unsigned size) override;
		bool midiAccepted() override { return true; }
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
			int32_t programs, params, inputs, outputs, flags;
			int* reserved1;
			int* reserved2;
			int32_t initialDelay, realQualitiesDeprecated, offQualitiesDeprecated;
			float ioRatioDeprecated;
			void* object;
			void* user;
			int32_t id, version;
			Process processReplacing;
		};
		typedef int* (Vst2xHostCallback)(Plugin* effect, int32_t opcode, int32_t index, int* value, void* data, float opt);
		class Buffer{
			public:
				Buffer(): _data(nullptr) {}
				~Buffer(){ destruct(); }
				void destruct(){
					if(!_data) return;
					for(unsigned i=0; i<_size; ++i) delete[] _data[i];
					delete[] _data;
				}
				void resize(unsigned n, unsigned m){
					destruct();
					_size=n;
					_data=new float*[_size];
					for(unsigned i=0; i<_size; ++i) _data[i]=new float[m];
				}
				float** data(){ return _data; }
			private:
				unsigned _size;
				float** _data;
		};
		static Vst2xHostCallback vst2xHostCallback;
		static std::map<Plugin*, Vst*> _self;
		static std::mutex _mutex;
		void setSelf(Plugin*);
		std::string getString(int32_t opcode, int32_t index);
		std::string show(unsigned duration=0, std::string expectationFileName="");
		Plugin* _plugin;
		Buffer _i, _o;
		std::atomic<uint64_t> _samples;
		std::atomic<double> _samplesPerBeat, _startToNowInQuarters, _lastBarToNowInQuarters;
		std::atomic<int32_t> _beatsPerBar, _beatsPerQuarter;
};

}//namespace dlal

#endif
