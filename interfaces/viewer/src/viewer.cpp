#include "viewer.hpp"

#include <sansation.hpp>

#include <sstream>
#include <algorithm>

const int S=8;

sf::Vector2f vector(int x, int y){ return sf::Vector2f((float)x, (float)y); }

Component::Component(){}

Component::Component(std::string name): _name(name) {}

void Component::render(sf::VertexArray& v){
	//self
	v.append(sf::Vertex(vector(_lX+S, _lY+S), sf::Color::Blue));
	v.append(sf::Vertex(vector(_lX-S, _lY+S), sf::Color::Blue));
	v.append(sf::Vertex(vector(_lX-S, _lY+S), sf::Color::Blue));
	v.append(sf::Vertex(vector(_lX-S, _lY-S), sf::Color::Blue));
	v.append(sf::Vertex(vector(_lX-S, _lY-S), sf::Color::Blue));
	v.append(sf::Vertex(vector(_lX+S, _lY-S), sf::Color::Blue));
	v.append(sf::Vertex(vector(_lX+S, _lY-S), sf::Color::Blue));
	v.append(sf::Vertex(vector(_lX+S, _lY+S), sf::Color::Blue));
	//connections
	for(auto i: _connections){
		if(i->_lY>_lY){
			v.append(sf::Vertex(
				vector(_lX, _lY+S),
				sf::Color::Red
			));
			v.append(sf::Vertex(
				vector(i->_lX, i->_lY-S),
				sf::Color::Green
			));
		}
		else{
			const unsigned POINTS=6;
			int dx=i->_lX>_lX?S:-S;
			int ex=i->_lX==_lX?dx:-dx;
			int points[POINTS*2]={
				_lX, _lY+S,
				_lX, _lY+S*2,
				_lX+2*dx, _lY+S*2,
				_lX+2*dx, i->_lY-2*S,
				i->_lX+ex, i->_lY-2*S,
				i->_lX   , i->_lY-S
			};
			for(unsigned j=0; j<POINTS-1; ++j){
				v.append(sf::Vertex(vector(points[2*(j+0)], points[2*(j+0)+1]),
					sf::Color(
						255-255*(j+0)/(POINTS-1),
						000+255*(j+0)/(POINTS-1),
						0
					)
				));
				v.append(sf::Vertex(vector(points[2*(j+1)], points[2*(j+1)+1]),
					sf::Color(
						255-255*(j+1)/(POINTS-1),
						000+255*(j+1)/(POINTS-1),
						0
					)
				));
			}
		}
	}
}

Viewer::Viewer(): _w(640), _h(480){
	if(!_font.loadFromMemory(sansation, sansationSize))
		throw std::runtime_error("couldn't load font");
}

void Viewer::process(std::string s){
	std::stringstream ss(s);
	while(ss>>s){
		if(s=="add"){
			ss>>s;
			_nameToComponent[s]=Component(s);
			layout();
		}
		else if(s=="connect"){
			ss>>s;
			std::string d;
			ss>>d;
			_nameToComponent[s]._connections.insert(&_nameToComponent[d]);
			_nameToComponent[s]._lKnownConnections.insert(&_nameToComponent[d]);
			layout();
		}
		else if(s=="disconnect"){
			ss>>s;
			std::string d;
			ss>>d;
			_nameToComponent[s]._connections.erase(&_nameToComponent[d]);
		}
	}
}

void Viewer::render(sf::RenderWindow& w){
	if(w.getSize().x!=_w||w.getSize().y!=_h){
		_w=w.getSize().x;
		_h=w.getSize().y;
		layout();
	}
	sf::VertexArray v(sf::Lines);
	for(auto i: _nameToComponent) i.second.render(v);
	w.draw(v);
}

void Viewer::layout(){
	//reset
	unsigned p=0, q=0;
	for(auto& i: _nameToComponent){
		i.second._lKnownConnecters.clear();
		i.second._lLaidout=false;
		i.second._lX=(5*p+3)*S;
		i.second._lY=(5*q+3)*S;
		++p;
		if((5*p+3)*S>_w-3*S){ p=0; ++q; }
	}
	//get connecters
	for(auto i: _nameToComponent)
		for(auto j: i.second._lKnownConnections)
			j->_lKnownConnecters.insert(&i.second);
	//count sources and sinks
	int sources=0, sinks=0;
	for(auto& i: _nameToComponent){
		if(i.second._lKnownConnecters.size()==0) ++sources;
		if(i.second._lKnownConnections.size()==0) ++sinks;
	}
	//layout sources and sinks
	int source=0, sink=0;
	for(auto& i: _nameToComponent){
		if(i.second._lKnownConnecters.size()==0){
			i.second._lX=_w*(source+1)/(sources+1);
			i.second._lY=3*S;
			i.second._lLaidout=true;
			++source;
		}
		if(i.second._lKnownConnections.size()==0){
			i.second._lX=_w*(sink+1)/(sinks+1);
			i.second._lY=_h-3*S;
			i.second._lLaidout=true;
			++sink;
		}
	}
	//layout one of the sourciest or sinkiest components if nothing is laidout
	if(sources==0&&sinks==0){
		auto j=_nameToComponent.begin();
		auto k=j;
		auto f=[j]()->unsigned{
			return std::min(
				j->second._lKnownConnecters.size(),
				j->second._lKnownConnections.size()
			);
		};
		unsigned m=f();
		while(j!=_nameToComponent.end()){
			if(f()<m){ m=f(); k=j; }
			++j;
		}
		k->second._lX=3*S;
		k->second._lY=3*S;
		if(k->second._lKnownConnecters.size()>k->second._lKnownConnections.size())
			k->second._lY=_h-3*S;
		k->second._lLaidout=true;
	}
	//layout the rest
	while(true){
		bool changed=false;
		for(auto& i: _nameToComponent) if(!i.second._lLaidout)
			for(auto j: i.second._lKnownConnections) if(j->_lLaidout){
				i.second._lX=j->_lX;
				i.second._lY=j->_lY-3*S;
				i.second._lLaidout=true;
				changed=true;
				break;
			}
		if(!changed) break;
	}
}
