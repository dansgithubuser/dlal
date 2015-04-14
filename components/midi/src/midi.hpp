#ifndef DLAL_MIDI_INCLUDED
#define DLAL_MIDI_INCLUDED

#include <skeleton.hpp>
#include <queue.hpp>

#include <RtMidi.h>

namespace dlal{

class Midi: public Component{
  public:
    Midi();
    ~Midi();
    void evaluate(unsigned samples);
    MidiMessages* readMidi();
    std::string* readText();
    void clearText();
    void sendText(const std::string&);
    std::string commands();
    void queue(const MidiMessage&);
  private:
    RtMidiIn* _rtMidiIn;
    Queue<MidiMessage> _queue;
    MidiMessages _messages;
    std::string _text;
};

}//namespace dlal

#endif
