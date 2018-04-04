#include "connection.hpp"

#include "component.hpp"

#include <algorithm>
#include <vector>

void Connection::draw(sf::VertexArray& va){
	int    midiHeat=int(512*   _midiHeat);
	int commandHeat=int(512*_commandHeat);
	_midiHeat   /=2;
	_commandHeat/=2;
	const sf::Color cn(std::min(255, midiHeat   ), std::min(255, commandHeat+64),  0, 128);
	const sf::Color cf(std::min(255, midiHeat+64), std::min(255, commandHeat+64),  0, 128);
	const sf::Color cb(std::min(255, midiHeat   ), std::min(255, commandHeat+64), 64, 128);
	std::vector<sf::Vertex> v;
	v.push_back(sf::Vertex(sf::Vector2f(_src->mouseX()+SZ, _src->mouseY()+2*SZ), cn));//source
	if(_dst->_y>_src->_y){//destination below
		if(_dst->_y-_src->_y<=5*SZ){//directly below
			v.push_back(sf::Vertex(sf::Vector2f(_src->mouseX()+SZ, _dst->mouseY()-SZ), cn));//drop to just above destination
		}
		else{
			v.push_back(sf::Vertex(sf::Vector2f(_src->mouseX()   , _src->mouseY()+3*SZ), cf));//diagonal
			v.push_back(sf::Vertex(sf::Vector2f(_src->mouseX()-SZ, _src->mouseY()+4*SZ), cf));//diagonal
			v.push_back(sf::Vertex(sf::Vector2f(_src->mouseX()-SZ, _dst->mouseY()-2*SZ), cf));//drop to just above destination
			v.push_back(sf::Vertex(sf::Vector2f(_src->mouseX()   , _dst->mouseY()-  SZ), cn));//diagonal
		}
	}
	else{
		v.push_back(sf::Vertex(sf::Vector2f(_src->mouseX()+2*SZ, _src->mouseY()+3*SZ), cn));//diagonal
		v.push_back(sf::Vertex(sf::Vector2f(_src->mouseX()+3*SZ, _src->mouseY()+2*SZ), cb));//diagonal
		v.push_back(sf::Vertex(sf::Vector2f(_src->mouseX()+3*SZ, _dst->mouseY()     ), cb));//align vertically
		v.push_back(sf::Vertex(sf::Vector2f(_src->mouseX()+2*SZ, _dst->mouseY()-  SZ), cn));//diagonal
	}
	v.push_back(sf::Vertex(sf::Vector2f(_dst->mouseX()+SZ, _dst->mouseY()-SZ), cn));//align horizontally
	v.push_back(sf::Vertex(sf::Vector2f(_dst->mouseX()+SZ, _dst->mouseY()   ), cn));//destination
	for(size_t i=0; i<v.size()-1; ++i){
		va.append(sf::Vertex(sf::Vector2f(v[i+0].position.x, v[i+0].position.y), v[i+0].color));
		va.append(sf::Vertex(sf::Vector2f(v[i+1].position.x, v[i+1].position.y), v[i+1].color));
	}
}
