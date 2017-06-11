//#define LOG_LAYOUT
//#define LOG_CHECK_LAYOUT
//#define RENDER_POINTERS

#include "viewer.hpp"

#include <courierCode.hpp>

#include <sstream>
#include <algorithm>
#include <functional>
#include <cassert>
#include <iostream>

#include <obvious.hpp>

static const int S=8;
#ifdef RENDER_POINTERS
	static const int H=12*S;
#else
	static const int H=5*S;
#endif
static const int V=5*S;

static const sf::Color colorComponent(0, 128, 0);
static const sf::Color colorForward(64, 64, 0);
static const sf::Color colorNormal(0, 64, 0);
static const sf::Color colorBackward(0, 64, 64);
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

struct Wire{
	Wire(){}
	Wire(Component* connecter, Component* connectee): connecter(connecter), connectee(connectee) {}
	bool operator<(const Wire& other) const{
		if(connecter<other.connecter) return true;
		if(connecter>other.connecter) return false;
		if(connectee<other.connectee) return true;
		return false;
	}
	Component* connecter;
	Component* connectee;
};

std::ostream& operator<<(std::ostream& o, const Wire& w){
	return o<<w.connecter<<" --> "<<w.connectee;
}

static bool checkLayout(const std::vector<Component*>& components){
	auto laidout=OBVIOUS_TRANSFORM(components, if((*i)->_laidout) r.push_back(*i), std::vector<Component*>());
	if(laidout.size()<2) return true;
	//check for overlapping components
	for(unsigned i=0; i<laidout.size(); ++i)
		for(unsigned j=i+1; j<laidout.size(); ++j){
			if(
				laidout.at(i)->_x==laidout.at(j)->_x
				&&
				laidout.at(i)->_y==laidout.at(j)->_y
			){
				#ifdef LOG_CHECK_LAYOUT
					std::cout<<"bad layout; "<<laidout.at(i)<<" and "<<laidout.at(j)<<" overlap\n";
				#endif
				return false;
			}
		}
	//figure out wiring layout
	int minX=0, minY=0, maxX=0, maxY=0;
	std::map<Pair, std::vector<Wire>> f, b, h;
	for(const auto& i: laidout){
		for(const auto& j: i->_connecters) if(j->_laidout){
			//align vertically
			if(i->_y>j->_y)//forward
				for(int y=j->_y+1; y<i->_y; ++y)
					f[Pair(j->_x, y)].push_back(Wire(j, i));
			else//backward
				for(int y=j->_y; y>=i->_y; --y)
					b[Pair(j->_x, y)].push_back(Wire(j, i));
			//align horizontally
			for(int x=OBVIOUS_MIN(i->_x, j->_x); x<=OBVIOUS_MAX(i->_x, j->_x); ++x)
				h[Pair(x, i->_y)].push_back(Wire(j, i));
			//max/min
		}
		OBVIOUS_MINI(minX, i->_x);
		OBVIOUS_MINI(minY, i->_y);
		OBVIOUS_MAXI(maxX, i->_x);
		OBVIOUS_MAXI(maxY, i->_y);
	}
	//simulate future wiring layout
	for(auto& i: laidout)
		for(auto& j: i->_connecters) if(!j->_laidout){
			++maxX; ++maxY;
			for(int y=maxY; y>=i->_y; --y) b[Pair(maxX, y)].push_back(Wire(j, i));
			for(int x=maxX; x>=i->_x; --x) h[Pair(x, i->_y)].push_back(Wire(j, i));
		}
	//check for ambiguous wiring
	std::set<Wire> overlapping;
	int x, y;
	auto checkWiring=[&](std::map<Pair, std::vector<Wire>> w, std::string type){
		auto wires=MAP_GET(w, Pair(x, y), std::vector<Wire>());
		if(!wires.empty()) overlapping+=wires;
		else{
			//we desire that overlapping wires
			//1: have the same connectees for each connecter
			//2: have the same connecters for each connectee
			std::map<Component*, std::set<Component*>> m, n;//map connecter to connectees and vice versa
			for(auto& i: overlapping){
				m[i.connecter].insert(i.connectee);
				n[i.connectee].insert(i.connecter);
			}
			decltype(m)::iterator ia, ib;
			if(!OBVIOUS_BINARY_TRANSFORM(m, (r&=a->second==b->second, OBVIOUS_IF(!r, (ia=a, ib=b))), true)){
				#ifdef LOG_CHECK_LAYOUT
					std::cout<<"bad layout; ambiguous "<<type<<" wiring at ("<<x<<", "<<y<<")\n";
					std::cout<<"\tconnecter "<<ia->first<<": connectees "<<ia->second<<"\n";
					std::cout<<"\tconnecter "<<ib->first<<": connectees "<<ib->second<<"\n";
				#endif
				return false;
			}
			if(!OBVIOUS_BINARY_TRANSFORM(n, (r&=a->second==b->second, OBVIOUS_IF(!r, (ia=a, ib=b))), true)){
				#ifdef LOG_CHECK_LAYOUT
					std::cout<<"bad layout; ambiguous "<<type<<" wiring at ("<<x<<", "<<y<<")\n";
					std::cout<<"\t connectee "<<ia->first<<": connecters "<<ia->second<<"\n";
					std::cout<<"\t connectee "<<ib->first<<": connecters "<<ib->second<<"\n";
				#endif
				return false;
			}
			overlapping.clear();
		}
		return true;
	};
	for(x=minX; x<=maxX; ++x){//vertical
		overlapping.clear();
		for(y=minY; y<=maxY+1; ++y){
			if(!checkWiring(f, "forward")) return false;
			if(!checkWiring(b, "backward")) return false;
		}
	}
	for(y=minY; y<=maxY; ++y){//horizontal
		overlapping.clear();
		for(x=minX; x<=maxX+2; ++x){
			if(!checkWiring(h, "horizontal")) return false;
		}
	}
	return true;
}

Component* findComponentToLayout(const std::vector<Component*> components){
	auto unlaidout=OBVIOUS_TRANSFORM(components, if(!(*i)->_laidout) r.push_back(*i), std::vector<Component*>());
	if(unlaidout.empty()) return nullptr;
	for(auto& i: unlaidout)//has laid-out connecter
		for(auto& j: i->_connecters) if(j->_laidout) return i;
	for(auto& i: unlaidout)//has laid-out connectee
		for(auto& j: i->_connections) if(j.second._component->_laidout) return i;
	return unlaidout.front();//fallback
}

#ifdef LOG_CHECK_LAYOUT
	#define LOG_CHECK_LAYOUT_TRYING_COMPONENT std::cout<<"trying "<<c<<" at ("<<c->_x<<", "<<c->_y<<")\n";
#else
	#define LOG_CHECK_LAYOUT_TRYING_COMPONENT
#endif

#define LAYOUT_TRY(METHOD)\
	LOG_CHECK_LAYOUT_TRYING_COMPONENT\
		if(checkLayout(components)){\
			c->noteLayout(METHOD);\
			return true;\
		}

static bool layout(Component* c, std::vector<Component*>& components){
	auto getLaidout=[&](){ return OBVIOUS_TRANSFORM(components, if((*i)->_laidout) r.push_back(*i), std::vector<Component*>()); };
	int minX=0, minY=0, maxX=0, maxY=0;
	for(auto& i: getLaidout()){
		OBVIOUS_MINI(minX, i->_x);
		OBVIOUS_MINI(minY, i->_y);
		OBVIOUS_MAXI(maxX, i->_x);
		OBVIOUS_MAXI(maxY, i->_y);
	}
	c->_laidout=true;
	//try to stick it directly below a connecter
	for(auto& i: c->_connecters)
		if(i->_laidout){
			c->_x=i->_x;
			c->_y=i->_y+1;
			LAYOUT_TRY("connecter")
		}
	//try to stick it directly above a connectee
	for(auto& i: c->_connections){
		auto j=i.second._component;
		if(j->_laidout){
			c->_x=j->_x;
			c->_y=j->_y-1;
			LAYOUT_TRY("connectee")
		}
	}
	//try to stick it somewhere within the laid-out universe
	for(int x=minX; x<=maxX; ++x)
		for(int y=minY; y<=maxY; ++y){
			c->_x=x;
			c->_y=y;
			LAYOUT_TRY("within")
		}
	//try to stick it below a connecter just beyond the universe
	for(auto& i: c->_connecters)
		if(i->_laidout){
			c->_x=maxX+1;
			c->_y=i->_y+1;
			LAYOUT_TRY("connecter-beyond")
		}
	//try to stick it above a connectee just beyond the universe
	for(auto& i: c->_connections){
		auto j=i.second._component;
		if(j->_laidout){
			c->_x=maxX+1;
			c->_y=j->_y-1;
			LAYOUT_TRY("connectee-beyond")
		}
	}
	//try to stick it just beyond the laid-out universe
	for(int x=minX; x<=maxX+1; ++x)
		for(int y=minY; y<=maxY+1; ++y){
			c->_x=x;
			c->_y=y;
			LAYOUT_TRY("beyond")
		}
	//failure
	for(auto& i: components) std::cout<<i<<": "<<i->_x<<", "<<i->_y<<" "<<(i->_laidout?"laid out":"")<<"\n";
	std::cout<<"couldn't lay out component\n";
	c->_laidout=false;
	return false;
}

static bool componentCompare(const Component* a, const Component* b){
	if(a->_type<b->_type) return true;
	if(a->_type>b->_type) return false;
	if(a->_label<b->_label) return true;
	if(a->_label>b->_label) return false;
	return a->_name<b->_name;
}

Component::Component(){}

Component::Component(std::string name, std::string type):
	_name(name), _phase(-1.0f), _heat(0.0f)
{
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

static void sketch(
	std::vector<sf::Vertex>& v, const char* s, int x, int y, sf::Color color
){
	unsigned i=0;
	while(s[i]!='\0'&&s[i+1]!='\0'){
		v.push_back(vertex(x+decode(s[i]), y+decode(s[i+1]), color));
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

void Component::renderLines(std::vector<sf::VertexArray>& v){
	v.resize(3, sf::VertexArray(sf::Lines));
	//self
	std::vector<sf::Vertex> u;
	sketch(u, "++-+--+-++", _x, _y, heat(colorComponent, _heat));
	_heat/=2.0f;
	stripToLines(u, v[1]);
	switch(_type){
		case AUDIO    : sketch(u, "=++==--==+", _x, _y, colorComponent); break;
		case BUFFER   : sketch(u, "-<+<+>->"  , _x, _y, colorComponent); break;
		case COMMANDER: sketch(u, "--+++--+"  , _x, _y, colorComponent); break;
		case LINER    : sketch(u, "-=+="      , _x, _y, colorComponent); break;
		case MIDI     : sketch(u, "--=++-"    , _x, _y, colorComponent); break;
		case NETWORK  : sketch(u, "--++"      , _x, _y, colorComponent); break;
		default: break;
	}
	stripToLines(u, v[1]);
	//phase
	if(_phase>=0.0f){
		float x=_x-S+2*S*_phase;
		v[1].append(sf::Vertex(sf::Vector2f(x, (float)_y-S), colorPhase));
		v[1].append(sf::Vertex(sf::Vector2f(x, (float)_y+S), colorPhase));
	}
	//connections
	std::vector<sf::Vertex> a, b;
	for(auto& i: _connections){
		if(i.second._on){
			auto dx=i.second._component->_x;
			auto dy=i.second._component->_y;
			sf::Color cn=heat(colorNormal, i.second._heat);
			u.push_back(vertex        (_x    , _y+  S, cn));//source
			if(dy>_y){//destination below
				if(dy-_y==V){//directly below
					u.push_back(vertex(_x    , dy-2*S, cn));//drop to just above destination
				}
				else{
					sf::Color cf=heat(colorForward, i.second._heat);
					u.push_back(vertex(_x-  S, _y+2*S, cf));/*diagonal*/
					u.push_back(vertex(_x-2*S, _y+3*S, cf));/*diagonal*/
					v[2].append(u.back());
					u.push_back(vertex(_x-2*S, dy-3*S, cf));/*drop to just above destination*/
					v[2].append(u.back());
					u.push_back(vertex(_x-  S, dy-2*S, cn));//diagonal
				}
			}
			else{
				sf::Color cb=heat(colorBackward, i.second._heat);
				u.push_back(vertex    (_x+  S, _y+2*S, cn));//diagonal
				u.push_back(vertex    (_x+2*S, _y+  S, cb));//diagonal
				v[0].append(u.back());
				u.push_back(vertex    (_x+2*S, dy-  S, cb));//align vertically
				v[0].append(u.back());
				u.push_back(vertex    (_x+  S, dy-2*S, cn));//diagonal
			}
			u.push_back(vertex        (dx    , dy-2*S, cn));//align horizontally
			u.push_back(vertex        (dx    , dy-  S, cn));//destination
			stripToLines(u, v[1]);
		}
		i.second._heat/=2.0f;
	}
}

void Component::renderText(sf::RenderWindow& w, const sf::Font& font){
	#ifdef RENDER_POINTERS
	{
		std::stringstream ss;
		ss<<this;
		sf::Text t(ss.str().c_str(), font, S);
		t.setPosition(1.0f*_x, 1.0f*_y+2*S);
		w.draw(t);
	}
	#endif
	if(!_label.size()) return;
	sf::Text t(_label.c_str(), font, S);
	t.setPosition(1.0f*_x, 1.0f*_y+S);
	w.draw(t);
}

void Component::noteLayout(std::string method){
	#ifdef LOG_LAYOUT
		std::cout<<this<<" laid out at ("<<_x<<", "<<_y<<") by "<<method<<" method.\n";
	#endif
}

std::ostream& operator<<(std::ostream& o, const Group& g){
	o<<g._components;
	return o;
}

Group::Group(Component* component){
	_components.push_back(component);
}

Group::Group(const std::map<std::string, Component::Connection>& map){
	for(const auto& i: map) _components.push_back(i.second._component);
	sort();
}

Group::Group(const std::set<Component*>& set){
	for(const auto& i: set) _components.push_back(i);
	sort();
}

Group::~Group(){
	if(_copy) for(auto& i: _components) delete i;
}

bool Group::similar(const Group& other) const{
	if(_components.size()!=other._components.size()) return false;
	auto similarInterconnect=[](const Group& a, const Group& ac, const Group& b, const Group& bc){
		if(ac._components.size()!=bc._components.size()) return false;
		for(unsigned i=0; i<ac._components.size(); ++i) if(
			index(ac._components.at(i), a._components)
			!=
			index(bc._components.at(i), b._components)
		) return false;
		return true;
	};
	for(unsigned i=0; i<_components.size(); ++i){
		auto a=_components.at(i), b=other._components.at(i);
		auto similarLabels=[](std::string a, std::string b){
			return a.substr(0, 3)==b.substr(0, 3);
		};
		if(!similarLabels(a->_label, b->_label)&&a->_type!=b->_type) return false;
		if(!similarInterconnect(*this, Group(a->_connections), other, Group(b->_connections))) return false;
		if(!similarInterconnect(*this, Group(a->_connecters ), other, Group(b->_connecters ))) return false;
	}
	return true;
}

bool Group::adjacent(const Group& other) const{
	for(const auto& i: _components){
		for(const auto& j: i->_connections) if(in(j.second._component, other._components)) return true;
		for(const auto& j: i->_connecters ) if(in(j                  , other._components)) return true;
	}
	return false;
}

void Group::merge(const Group& other){
	_components.insert(_components.end(), other._components.begin(), other._components.end());
	sort();
}

Group Group::copy() const{
	Group r;
	r._copy=true;
	r=*this;
	std::map<Component*, Component*> m;
	for(auto& i: r._components){
		m[i]=new Component(*i);
		i=m.at(i);
	}
	for(auto& j: r._components){
		j->_connecters=OBVIOUS_TRANSFORM(j->_connecters, r.insert(MAP_GET(m, *i, *i)), std::set<Component*>());
		for(auto& i: j->_connections) if(m.count(i.second._component)) i.second._component=m.at(i.second._component);
	}
	return r;
}

void Group::sort(){
	std::sort(_components.begin(), _components.end(), componentCompare);
}

Viewer::Viewer(): _w(0), _h(0) {
	if(!_font.loadFromMemory(courierCode, courierCodeSize))
		throw std::runtime_error("couldn't load font");
}

void Viewer::printLayout() const{
	std::cout<<"layout:\n";
	for(auto& i: _nameToComponent) std::cout<<i.second<<": "<<i.second->_x<<", "<<i.second->_y<<" "<<(i.second->_laidout?"laid out":"")<<"\n";
	std::cout<<"end of layout\n";
}

void Viewer::process(std::string s){
	auto connect=[this](std::string s, std::string d){
		if(_nameToComponent[s]->_connections.count(d)) _nameToComponent[s]->_connections[d]._on=true;
		else _nameToComponent[s]->_connections[d]=_nameToComponent[d];
	};
	std::stringstream ss(s);
	while(ss>>s){
		static std::map<std::string, std::function<void()>> handlers={
			{"add", [&](){
				ss>>s;
				std::string t;
				ss>>t;
				if(!_nameToComponent.count(s)){
					_nameToComponent[s]=new Component(s, t);
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
				assert(_nameToComponent[s]->_connections.count(d));
				_nameToComponent[s]->_connections[d]._on=false;
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
				ss>>_nameToComponent[s]->_label;
			}},
			{"command", [&](){
				ss>>s;
				if(!_nameToComponent.count(s)) return;
				_nameToComponent[s]->_heat+=0.5f;
				std::string d;
				ss>>d;
				if(!_nameToComponent.count(d)) return;
				_nameToComponent[d]->_heat+=0.5f;
				if(!_nameToComponent[s]->_connections.count(d)) return;
				_nameToComponent[s]->_connections[d]._heat+=0.5f;
			}},
			{"midi", [&](){
				ss>>s;
				if(!_nameToComponent.count(s)) return;
				std::string d;
				ss>>d;
				if(!_nameToComponent[s]->_connections.count(d)) return;
				_nameToComponent[s]->_connections[d]._heat+=0.5f;
			}},
			{"phase", [&](){
				ss>>s;
				if(!_nameToComponent.count(s)) return;
				ss>>_nameToComponent[s]->_phase;
			}},
			{"edge", [&](){
				ss>>s;
				if(!_nameToComponent.count(s)) return;
				_nameToComponent[s]->_phase=0.0f;
			}}
		};
		ss>>std::ws;
		if(s!="edge"&&s!="phase"){
			_reports.push_back(s);
			if(_reports.size()>8) _reports.pop_front();
		}
		if(handlers.count(s)) handlers[s]();
	}
}

void Viewer::render(sf::RenderWindow& wv, sf::RenderWindow& wt){
	const float line_space=18.0f;
	const int text_height=12;
	const float margin=6.0f;
	float y=0.0f;
	//variables
	for(const auto& i: _variables){
		std::string s=i.first+": "+i.second;
		sf::Text t(s.c_str(), _font, text_height);
		t.setPosition(margin, y);
		wt.draw(t);
		y+=line_space;
	}
	y+=18.0f;
	//reports
	for(const auto& i: _reports){
		sf::Text t(i.c_str(), _font, text_height);
		t.setPosition(margin, y);
		wt.draw(t);
		y+=line_space;
	}
	//relayout if resized
	if(wv.getSize().x!=_w||wv.getSize().y!=_h){
		_w=wv.getSize().x;
		_h=wv.getSize().y;
		layout();
	}
	//components
	std::vector<sf::VertexArray> v;
	for(auto& i: _nameToComponent) i.second->renderLines(v);
	for(auto& i: v) wv.draw(i);
	for(auto& i: _nameToComponent) i.second->renderText(wv, _font);
}

void Viewer::layout(){
	bool failed=false;
	//reset
	#if defined(LOG_LAYOUT)
		OBVIOUS_LOUD("starting new layout")
	#endif
	for(auto& i: _nameToComponent){
		i.second->_connecters.clear();
		i.second->_laidout=false;
	}
	//get connecters
	for(auto& i: _nameToComponent)
		for(auto& j: i.second->_connections)
			j.second._component->_connecters.insert(i.second);
	//initial groups
	std::vector<Group> groups;
	{
		auto components=OBVIOUS_TRANSFORM(_nameToComponent, r.push_back(i->second), std::vector<Component*>());
		std::sort(components.begin(), components.end(), componentCompare);
		for(auto& i: components) groups.push_back(Group(i));
	}
	//refine groups
	while(true){
		//only keep groups that are similar to some other group
		for(unsigned i=0; i<groups.size(); /*nothing*/){
			bool similar=false;
			for(unsigned j=0; j<groups.size(); ++j)
				if(i!=j&&groups.at(i).similar(groups.at(j))){
					similar=true;
					break;
				}
			if(similar) ++i;
			else groups.erase(groups.begin()+i);
		}
		//merge adjacent groups (initial group ordering ensures this is sensible)
		bool done=true;
		for(unsigned i=0; i<groups.size(); ++i)
			for(unsigned j=i+1; j<groups.size(); /*nothing*/){
				if(groups.at(i).adjacent(groups.at(j))){
					groups.at(i).merge(groups.at(j));
					groups.erase(groups.begin()+j);
					done=false;
				}
				else ++j;
			}
		if(done) break;
	}
	//remove size-1 groups
	groups=OBVIOUS_FILTER(groups, i->_components.size()>1);
	//sort by number of similar groups
	std::vector<std::vector<Group>> groupings;
	for(const auto& i: groups){
		bool fit=false;
		for(unsigned j=0; j<groupings.size(); ++j)
			if(i.similar(groupings.at(j).at(0))){
				groupings.at(j).push_back(i);
				fit=true;
				break;
			}
		if(!fit) groupings.push_back({i});
	}
	std::sort(groupings.begin(), groupings.end(),
		[](const std::vector<Group>& a, const std::vector<Group>& b){
			return a.size()>b.size();
		}
	);
	//layout groupings
	for(auto& grouping: groupings){
		#if defined(LOG_LAYOUT)
			std::cout<<"laying out grouping:\n"<<grouping<<"\n";
		#endif
		//create a summary group
		auto summary=grouping.at(0).copy();
		for(auto& group: grouping)//for each group
			for(unsigned i=0; i<summary._components.size(); ++i){//for each component
				auto summaryComponent=summary._components.at(i);
				auto groupComponent=group._components.at(i);
				//contribute connectees to summary
				for(auto& i: groupComponent->_connections)
					if(
						!in(i.second._component, group._components)
						&&
						!in(i.second._component, OBVIOUS_TRANSFORM(summaryComponent->_connections, r.push_back(i->second._component), std::vector<Component*>()))
					) summaryComponent->_connections[i.first]=i.second;
				//contribute connecters to summary
				for(auto& i: groupComponent->_connecters)
					if(!in(i, group._components))
						summaryComponent->_connecters.insert(i);
			}
		//layout the summary
		#if defined(LOG_LAYOUT)
			std::cout<<"laying out summary: "<<summary._components<<"\n";
		#endif
		while(!failed){
			auto component=findComponentToLayout(summary._components);
			if(!component) break;
			if(!::layout(component, summary._components)) failed=true;
		}
		if(failed) break;
		//copy the layout back
		for(auto& i: grouping)
			for(unsigned j=0; j<summary._components.size(); ++j){
				i._components.at(j)->_x=summary._components.at(j)->_x;
				i._components.at(j)->_y=summary._components.at(j)->_y;
			}
		for(auto& group: grouping){
			#if defined(LOG_LAYOUT)
				std::cout<<"laying out group: "<<group<<"\n";
			#endif
			layout(group);
		}
	}
	//layout
	auto components=OBVIOUS_TRANSFORM(_nameToComponent, r.push_back(i->second), std::vector<Component*>());
	std::sort(components.begin(), components.end(), componentCompare);
	while(!failed){
		auto component=findComponentToLayout(components);
		if(!component) break;
		#if defined(LOG_LAYOUT)
			std::cout<<"laying out component: "<<component<<"\n";
		#endif
		if(!layout(component)) failed=true;
	}
	//failure recovery
	if(failed){
		int x=OBVIOUS_TRANSFORM(_nameToComponent, if(i->second->_laidout) OBVIOUS_MAXI(r, i->second->_x), 0)+2;
		int y=OBVIOUS_TRANSFORM(_nameToComponent, if(i->second->_laidout) OBVIOUS_MAXI(r, i->second->_y), 0)+2;
		for(auto& i: _nameToComponent) if(!i.second->_laidout){ i.second->_x=x++; i.second->_y=y++; }
	}
	//logical coordinates to pixels
	for(auto& i: _nameToComponent){
		i.second->_x=(i.second->_x+1)*H;
		i.second->_y=(i.second->_y+1)*V;
	}
}

void Viewer::layout(Group& g){
	//get size of group to use as stride
	int dX=OBVIOUS_TRANSFORM(g._components, OBVIOUS_MAXI(r, (*i)->_x), 0)+1;
	int dY=OBVIOUS_TRANSFORM(g._components, OBVIOUS_MAXI(r, (*i)->_y), 0)+1;
	//layout in +xy, preferring minimal distance
	for(auto& i: g._components) i->_laidout=true;
	unsigned d=0;
	while(true){
		for(unsigned e=0; e<=d; ++e){
			unsigned x=dX*(d-e);
			unsigned y=dY*e;
			for(auto& i: g._components) i->_x+=x;
			for(auto& i: g._components) i->_y+=y;
			#ifdef LOG_CHECK_LAYOUT
				for(auto& i: g._components) std::cout<<"trying "<<i<<" at ("<<i->_x<<", "<<i->_y<<")\n";
			#endif
			if(checkLayout(OBVIOUS_TRANSFORM(_nameToComponent, r.push_back(i->second), std::vector<Component*>()))){
				for(auto& i: g._components) i->noteLayout("group");
				normalizeCoords();
				return;
			}
			for(auto& i: g._components) i->_y-=y;
			for(auto& i: g._components) i->_x-=x;
		}
		++d;
	}
}

bool Viewer::layout(Component* c){
	auto x=OBVIOUS_TRANSFORM(_nameToComponent, r.push_back(i->second), std::vector<Component*>());
	bool r=::layout(c, x);
	normalizeCoords();
	return r;
}

void Viewer::normalizeCoords(){
	int minX=OBVIOUS_TRANSFORM(_nameToComponent, if(i->second->_laidout) OBVIOUS_MINI(r, i->second->_x), 0);
	int minY=OBVIOUS_TRANSFORM(_nameToComponent, if(i->second->_laidout) OBVIOUS_MINI(r, i->second->_y), 0);
	for(auto& i: _nameToComponent){
		i.second->_x-=minX;
		i.second->_y-=minY;
	}
}
