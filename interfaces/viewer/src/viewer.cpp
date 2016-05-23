#include "viewer.hpp"

#include <courierCode.hpp>

#include <sstream>
#include <algorithm>
#include <functional>
#include <cassert>

static const int S=8;

static const sf::Color colorComponent(0, 128, 0);
static const sf::Color colorForward(0, 64, 64);
static const sf::Color colorNormal(0, 64, 0);
static const sf::Color colorBackward(64, 64, 0);
static const sf::Color colorPhase(0, 0, 255);

static sf::Vertex vertex(int x, int y, const sf::Color& color){
	return sf::Vertex(sf::Vector2f((float)x, (float)y), color);
}

static void stripToLines(
	std::vector<sf::Vertex>& u, sf::VertexArray& v
){
	if(!u.size()) return;
	for(unsigned i=0; i<u.size()-1; ++i){
		v.append(u[i+0]);
		v.append(u[i+1]);
	}
	u.clear();
}

Component::Component(){}

Component::Component(std::string name, std::string type): _name(name), _phase(-1.0f) {
	if(type=="audio") _type=AUDIO;
	else if(type=="buffer") _type=BUFFER;
	else if(type=="commander") _type=COMMANDER;
	else if(type=="liner") _type=LINER;
	else if(type=="midi") _type=MIDI;
	else if(type=="network") _type=NETWORK;
	else _type=OTHER;
}

static int decode(char c){
	switch(c){
		case '-': return -S;
		case '<': return -S/2;
		case '=': return 0;
		case '>': return S/2;
		case '+': return S;
		default: break;
	}
	return 0;
}

static void sketch(std::vector<sf::Vertex>& v, const char* s, int x, int y){
	unsigned i=0;
	while(s[i]!='\0'&&s[i+1]!='\0'){
		v.push_back(vertex(x+decode(s[i]), y+decode(s[i+1]), colorComponent));
		i+=2;
	}
}

static sf::Color heat(const sf::Color& base, float heat){
	sf::Color result;
	result.r=(sf::Uint8)std::min(255.0f, base.r+255*heat);
	result.g=(sf::Uint8)std::min(255.0f, base.g+255*heat);
	result.b=(sf::Uint8)std::min(255.0f, base.b+255*heat);
	return result;
}

void Component::renderLines(sf::VertexArray& v){
	//self
	std::vector<sf::Vertex> u;
	sketch(u, "++-+--+-++", _x, _y);
	stripToLines(u, v);
	switch(_type){
		case AUDIO: sketch(u, "=++==--==+", _x, _y); break;
		case BUFFER: sketch(u, "-<+<+>->", _x, _y); break;
		case COMMANDER: sketch(u, "--+++--+", _x, _y); break;
		case LINER: sketch(u, "-=+=", _x, _y); break;
		case MIDI: sketch(u, "--=++-", _x, _y); break;
		case NETWORK: sketch(u, "--++", _x, _y); break;
		default: break;
	}
	stripToLines(u, v);
	//phase
	if(_phase>=0.0f){
		float x=_x-S+2*S*_phase;
		v.append(sf::Vertex(sf::Vector2f(x, (float)_y-S), colorPhase));
		v.append(sf::Vertex(sf::Vector2f(x, (float)_y+S), colorPhase));
	}
	//connections
	for(auto& i: _connections){
		if(i.second._on){
			auto dx=i.second._component->_x;
			auto dy=i.second._component->_y;
			sf::Color cn=heat(colorNormal, i.second._heat);
			u.push_back(vertex    (_x    , _y+  S, cn));//source
			if(dy>_y){//destination below
				sf::Color cf=heat(colorForward, i.second._heat);
				u.push_back(vertex  (_x-  S, _y+2*S, cf));//diagonal
				u.push_back(vertex  (_x-  S, dy-3*S, cf));//drop to just above destination
				u.push_back(vertex  (_x    , dy-2*S, cn));//diagonal
				u.push_back(vertex  (dx    , dy-2*S, cn));//align horizontally
			}
			else{
				sf::Color cb=heat(colorBackward, i.second._heat);
				u.push_back(vertex  (_x+  S, _y+2*S, cn));//diagonal
				u.push_back(vertex  (_x+2*S, _y+  S, cb));//diagonal
				u.push_back(vertex  (_x+2*S, dy-  S, cb));//align vertically
				u.push_back(vertex  (_x+  S, dy-2*S, cn));//diagonal
				u.push_back(vertex  (dx    , dy-2*S, cn));//align horizontally
			}
			u.push_back(vertex    (dx    , dy-  S, cn));//destination
			stripToLines(u, v);
		}
		i.second._heat/=2.0f;
	}
}

void Component::renderText(sf::RenderWindow& w, const sf::Font& font){
	if(!_label.size()) return;
	sf::Text t(_label.c_str(), font, S);
	t.setPosition(1.0f*_x, 1.0f*_y);
	w.draw(t);
}

Viewer::Viewer(): _w(0), _h(0) {
	if(!_font.loadFromMemory(courierCode, courierCodeSize))
		throw std::runtime_error("couldn't load font");
}

void Viewer::process(std::string s){
	auto connect=[this](std::string s, std::string d){
		if(_nameToComponent[s]._connections.count(d)) _nameToComponent[s]._connections[d]._on=true;
		else _nameToComponent[s]._connections[d]=_nameToComponent[d];
	};
	std::stringstream ss(s);
	while(ss>>s){
		static std::map<std::string, std::function<void()>> handlers={
			{"add", [&](){
				ss>>s;
				std::string t;
				ss>>t;
				if(!_nameToComponent.count(s)){
					_nameToComponent[s]=Component(s, t);
					for(unsigned i=0; i<_pendingConnections.size(); /*nothing*/){
						if(_nameToComponent.count(_pendingConnections[i].first)&&_nameToComponent.count(_pendingConnections[i].second)){
							connect(_pendingConnections[i].first, _pendingConnections[i].second);
							_pendingConnections[i]=_pendingConnections.back();
							_pendingConnections.pop_back();
						}
						else ++i;
					}
					layout();
				}
			}},
			{"connect", [&](){
				ss>>s;
				std::string d;
				ss>>d;
				if(_nameToComponent.count(s)&&_nameToComponent.count(d)){
					connect(s, d);
					layout();
				}
				else _pendingConnections.push_back(std::pair<std::string, std::string>(s, d));
			}},
			{"disconnect", [&](){
				ss>>s;
				assert(_nameToComponent.count(s));
				std::string d;
				ss>>d;
				assert(_nameToComponent[s]._connections.count(d));
				_nameToComponent[s]._connections[d]._on=false;
			}},
			{"variable", [&](){
				std::getline(ss, s);
				std::string v;
				std::getline(ss, v);
				_variables[s]=v;
			}},
			{"label", [&](){
				ss>>s;
				assert(_nameToComponent.count(s));
				ss>>_nameToComponent[s]._label;
			}},
			{"command", [&](){
				ss>>s;
				if(!_nameToComponent.count(s)) return;
				std::string d;
				ss>>d;
				if(!_nameToComponent[s]._connections.count(d)) return;
				_nameToComponent[s]._connections[d]._heat+=0.5f;
			}},
			{"midi", [&](){
				ss>>s;
				if(!_nameToComponent.count(s)) return;
				std::string d;
				ss>>d;
				if(!_nameToComponent[s]._connections.count(d)) return;
				_nameToComponent[s]._connections[d]._heat+=0.5f;
			}},
			{"phase", [&](){
				ss>>s;
				if(!_nameToComponent.count(s)) return;
				ss>>_nameToComponent[s]._phase;
			}},
			{"edge", [&](){
				ss>>s;
				if(!_nameToComponent.count(s)) return;
				_nameToComponent[s]._phase=0.0f;
			}}
		};
		ss>>std::ws;
		if(handlers.count(s)) handlers[s]();
	}
}

void Viewer::render(sf::RenderWindow& wv, sf::RenderWindow& wt){
	//variables
	float y=0.0f;
	for(auto& i: _variables){
		std::string s=i.first+": "+i.second;
		sf::Text t(s.c_str(), _font, 12);
		t.setPosition(6.0f, y);
		wt.draw(t);
		y+=18.0f;
	}
	//relayout if resized
	if(wv.getSize().x!=_w||wv.getSize().y!=_h){
		_w=wv.getSize().x;
		_h=wv.getSize().y;
		layout();
	}
	//components
	sf::VertexArray v(sf::Lines);
	for(auto& i: _nameToComponent) i.second.renderLines(v);
	wv.draw(v);
	for(auto& i: _nameToComponent) i.second.renderText(wv, _font);
}

class Layouter{
	/*
	components must have unique (x, y)
	components must have unique x and unique y, except
		components with identical connecters may share y
		a connecter and connectee may share x if the connecter has only that connection
			connectee must go below connecter
	*/
	public:
		Layouter(): minX(0), minY(0) {}

		void layout(Component& component, int x, int y){
			//try potential points in an order that emanates in (+x, +y), and prefers horizontal>vertical>diagonal
			int px, py, rung=0, step=0;
			bool sense=false;
			while(true){
				px=x+(sense?rung-step/2:step/2);
				py=y+(sense?step/2:rung-step/2);
				if(
					!taken.count(Point(px, py))
					&&(
						!xToBottom.count(px)
						||(
							xToBottom[px]->_connections.size()==1//connecter has only 1 connectee
							&&xToBottom[px]->_connections.begin()->second._component==&component//connecter connects to connectee
						)
					)
				){
					if(!yToConnecters.count(py)) break;
					//these copies need to be made because of some weakass C++ or MSVC bullshit
					//try it, I dare you
					//if(*yToConnecters[py]==component._connecters) break;
					auto a=*yToConnecters[py];
					auto b=component._connecters;
					if(a==b) break;
				}
				sense=!sense;
				++step;
				if(step>rung){ sense=false; step=0; ++rung; }
			}
			//assign this spot to the component
			x=px; y=py;
			xToBottom[x]=&component;
			yToConnecters[y]=&component._connecters;
			taken.insert(Point(x, y));
			minX=std::min(minX, x);
			minY=std::min(minY, y);
			component._x=x;
			component._y=y;
			component._laidout=true;
		};

		typedef std::pair<int, int> Point;
		std::set<Point> taken;
		std::map<int, Component*> xToBottom;
		std::map<int, std::set<Component*>*> yToConnecters;
		int minX, minY;
};

void Viewer::layout(){
	//reset
	for(auto& i: _nameToComponent){
		i.second._connecters.clear();
		i.second._laidout=false;
	}
	//get connecters
	for(auto& i: _nameToComponent)
		for(auto& j: i.second._connections)
			j.second._component->_connecters.insert(&i.second);
	//find sourcey components
	std::vector<Component*> sourceys;
	{
		auto minConnecters=_nameToComponent.size()+1;
		for(auto& i: _nameToComponent) minConnecters=std::min(i.second._connecters.size(), minConnecters);
		for(auto& i: _nameToComponent) if(i.second._connecters.size()==minConnecters) sourceys.push_back(&i.second);
	}
	//find sinks
	std::set<Component*> sinks;
	for(auto& i: _nameToComponent) if(i.second._connections.size()==0) sinks.insert(&i.second);
	//
	Layouter layouter;
	for(auto& i: sourceys) layouter.layout(*i, 0, 0);
	while(true){
		Component* component=NULL;
		Component* connecter;
		//try to get an unlaidout nonsink with a laidout connecter
		for(auto& i: _nameToComponent){
			if(i.second._laidout) continue;
			if(sinks.count(&i.second)) continue;
			connecter=NULL;
			for(auto& j: i.second._connecters) if(j->_laidout){ connecter=j; break; }
			if(connecter){ component=&i.second; break; }
		}
		//if there isn't one, we're done, otherwise layout
		if(!component) break;
		layouter.layout(*component, connecter->_x, connecter->_y);
	}
	//sinks
	for(auto& i: _nameToComponent){
		if(i.second._laidout) continue;
		Component* j=*i.second._connecters.begin();
		layouter.layout(i.second, j->_x, j->_y);
	}
	//logical coordinates to pixels
	for(auto& i: _nameToComponent){
		i.second._x=(i.second._x-layouter.minX+1)*S*4;
		i.second._y=(i.second._y-layouter.minY+1)*S*5;
	}
}
