#ifndef CONNECTION_HPP_INCLUDED
#define CONNECTION_HPP_INCLUDED

#include <wrapper.hpp>

struct Component;

struct Connection{
	Connection(){}
	Connection(Component* src, Component* dst): _src(src), _dst(dst) {}

	void draw(sf::VertexArray& va);

	Component* _src;
	Component* _dst;
	float _commandHeat=0.0f, _midiHeat=0.0f;
};

#endif
