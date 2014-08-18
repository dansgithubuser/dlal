#ifndef DLAL_MIDI_INCLUDED
#define DLAL_MIDI_INCLUDED

#include <functional>
#include <vector>

namespace dlal{

void midiInit(std::function<void(std::vector<unsigned char>&)>);
void midiFinish();

}//namespace dlal

#endif
