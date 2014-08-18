#ifndef DLAL_AUDIO_INCLUDED
#define DLAL_AUDIO_INCLUDED

#include <functional>

namespace dlal{

void audioInit(
	std::function<void(const float* input, float* output)> callback,
	unsigned sampleRate,
	unsigned log2SamplesPerCallback
);

void audioFinish();

}//namespace dlal

#endif
