#ifndef DLAL_SKELETON_INCLUDED
#define DLAL_SKELETON_INCLUDED

#include <cstdint>
#include <string>
#include <vector>

extern "C"{
	//each component implements this
	//return a new instance casted to dlal::Component*
  void* dlalBuildComponent();

	//implemented by skeleton
	void* dlalBuildSystem();
  const char* dlalQueryComponent(void* component);
  const char* dlalCommandComponent(void* component, const char* command);
  const char* dlalAddComponent(void* system, void* component);
  const char* dlalConnectComponents(void* input, void* output);
}

namespace dlal{

class Component;

class System{
	public:
		void addComponent(Component& component);
		void evaluate(unsigned samples);
	private:
		std::vector<Component*> _components;
};

struct MidiMessage{
  static const unsigned SIZE=4;
  MidiMessage();
  MidiMessage(const std::vector<uint8_t>&);
  uint8_t _bytes[SIZE];
};

class MidiMessages{
  public:
    MidiMessages();
    MidiMessage& operator[](unsigned);
    const MidiMessage& operator[](unsigned) const;
    unsigned size() const;
    bool push_back(const MidiMessage&);
    void clear();
  private:
    static const unsigned SIZE=256;
    MidiMessage _messages[SIZE];
    unsigned _size;
};

class Component{
	public:
    Component(): _system(NULL) {}
    virtual ~Component(){}
    virtual bool ready(){ return true; }
		virtual void addInput(Component*){}
    virtual void addOutput(Component*){}
		virtual void evaluate(unsigned samples){}
		virtual float* readAudio(){ return nullptr; }
		virtual MidiMessages* readMidi(){ return nullptr; }
		virtual std::string* readText(){ return nullptr; }
    virtual void clearText(){}
		virtual bool sendText(const std::string&){ return false; }
    virtual std::string commands(){ return ""; }
		System* _system;
};

}//namespace dlal

#endif//#ifndef DLAL_SKELETON_INCLUDED
