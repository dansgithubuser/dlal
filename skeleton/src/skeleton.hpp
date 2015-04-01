#ifndef DLAL_SKELETON_INCLUDED
#define DLAL_SKELETON_INCLUDED

#include <cstdint>
#include <string>
#include <map>
#include <vector>

extern "C"{
	//each component implements this
	//return a new instance casted to dlal::Component*
  void* dlalBuildComponent();

	//implemented by skeleton
	void* dlalBuildSystem();
  const char* dlalAddComponent(void* system, void* component, const char* name);
  const char* dlalConnectComponents(void* system, const char* nameInput, const char* nameOutput);
  const char* dlalCommandComponent(void* system, const char* name, const char* command);
}

namespace dlal{

class Component;

class System{
	public:
		std::string addComponent(Component& component, const std::string& name);
		std::string connectComponents(const std::string& nameInput, const std::string& nameOutput);
		std::string commandComponent(const std::string& name, const std::string& command);
		void evaluate(unsigned samples);
	private:
		std::map<std::string, Component*> _components;
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
    virtual ~Component(){}
		virtual void addInput(Component*){}
    virtual void addOutput(Component*){}
		virtual void evaluate(unsigned samples){}
		virtual float* readAudio(){ return nullptr; }
		virtual MidiMessages* readMidi(){ return nullptr; }
		virtual std::string* readText(){ return nullptr; }
		virtual void sendText(const std::string&){}
		System* _system;
};

}//namespace dlal

#endif//#ifndef DLAL_SKELETON_INCLUDED
