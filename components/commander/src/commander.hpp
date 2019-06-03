#ifndef DLAL_COMMANDER_INCLUDED
#define DLAL_COMMANDER_INCLUDED

#include <skeleton.hpp>

#include <atomic>
#include <sstream>
#include <vector>

namespace dlal{

class Commander: public MultiOut, public Periodic{
	public:
		struct Directive{
			enum Type{ COMMAND, COMMAND_INDEXED, ADD, CONNECT, DISCONNECT };
			Directive();
			Directive(Component&, const std::string& command, unsigned edgesToWait);
			Directive(unsigned i, const std::string& command, unsigned edgesToWait);
			Directive(Component&, unsigned slot, unsigned edgesToWait);
			Directive(Component& input, Component& output, unsigned edgesToWait);
			Directive& disconnect(){ _type=DISCONNECT; return *this; }
			std::string str() const;
			void dstr(std::stringstream&);
			Type _type;
			std::string _command;
			std::string _nameA, _nameB;
			Component* _a=nullptr;
			Component* _b=nullptr;
			unsigned _slot, _edgesToWait, _output;
		};
		Commander();
		std::string type() const override { return "commander"; }
		void* derived() override { return this; }
		std::string prep() override;
		void evaluate() override;
		Queue<Directive> _queue;
	private:
		void dispatch(Directive&);
		std::vector<Directive> _dequeued;
		unsigned _nDequeued;
		std::vector<std::vector<Directive>> _slots;
		size_t _slot=0;
		bool _slotsEnable=true;
};

}//namespace dlal

#endif
