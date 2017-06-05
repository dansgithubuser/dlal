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

/*
(1) components must have unique (x, y)
(2) components must have unique x and unique y, except
	(2.1) components with no connecters may share y with any other component
	(2.2) components with identical connecters may share y
	(2.3) components with no connectees may share x with any other component
	(2.4) components with identical or no connectees other than a chain linking them may share x
*/
static bool checkLayout(const std::vector<Component*>& c){
	if(c.size()<2) return true;
	for(unsigned i=0; i<c.size(); ++i)
		for(unsigned j=i+1; j<c.size(); ++j){
			//(1)
			if(
				c.at(i)->_x==c.at(j)->_x
				&&
				c.at(i)->_y==c.at(j)->_y
			){
				#ifdef LOG_CHECK_LAYOUT
					std::cout<<"bad layout; "<<c.at(i)<<" and "<<c.at(j)<<" overlap\n";
				#endif
				return false;
			}
			//(2)
			if(c.at(i)->_y==c.at(j)->_y)
				if(!c.at(i)->_connecters.empty()&&!c.at(j)->_connecters.empty())//(2.1)
					if(c.at(i)->_connecters!=c.at(j)->_connecters){//(2.2)
						#ifdef LOG_CHECK_LAYOUT
							std::cout<<"bad layout; "<<c.at(i)<<" and "<<c.at(j)<<" cannot share y\n";
						#endif
						return false;
					}
			if(c.at(i)->_x==c.at(j)->_x)
				if(!c.at(i)->_connections.empty()&&!c.at(j)->_connections.empty()){//(2.3)
					//(2.4)
					//get column
					std::vector<Component*> column;
					for(auto& k: c) if(k->_x==c.at(i)->_x) column.push_back(k);
					std::sort(column.begin(), column.end(), [](const Component* a, const Component* b){ return a->_y<b->_y; });
					//helper for getting connectees
					auto getConnectees=[](Component* c){
						return OBVIOUS_TRANSFORM(c->_connections, r.insert(i->second._component), std::set<Component*>());
					};
					//get connectees of final element
					auto connectees=getConnectees(column.back());
					//go through pairs
					for(unsigned k=0; k<column.size()-1; ++k){
						//get connectees other than chain link
						auto x=getConnectees(column.at(k));
						if(column.at(k+1)->_y-column.at(k)->_y==1) x.erase(column.at(k+1));
						//make sure identical or no connectees
						if(connectees.empty()) connectees=x;
						else if(!x.empty()&&connectees!=x){
							#ifdef LOG_CHECK_LAYOUT
								std::cout<<"bad layout; "<<c.at(i)<<" and "<<c.at(j)<<" cannot share x\n";
							#endif
							return false;
						}
					}
				}
		}
	return true;
}

static void layout(Component* c, std::vector<Component*>& components){
	auto getLaidout=[&](){ return OBVIOUS_TRANSFORM(components, if((*i)->_laidout) r.push_back(*i), std::vector<Component*>()); };
	int minX=0, minY=0, maxX=0, maxY=0;
	for(auto& i: getLaidout()){
		OBVIOUS_MIN(minX, i->_x);
		OBVIOUS_MIN(minY, i->_y);
		OBVIOUS_MAX(maxX, i->_x);
		OBVIOUS_MAX(maxY, i->_y);
	}
	c->_laidout=true;
	auto laidout=getLaidout();
	//try to stick it directly below a connecter
	for(auto& i: c->_connecters)
		if(i->_laidout){
			c->_x=i->_x;
			c->_y=i->_y+1;
			if(checkLayout(laidout)){
				c->noteLayout("connecter");
				return;
			}
		}
	//try to stick it directly above a connectee
	for(auto& i: c->_connections){
		auto j=i.second._component;
		if(j->_laidout){
			c->_x=j->_x;
			c->_y=j->_y-1;
			if(checkLayout(laidout)){
				c->noteLayout("connectee");
				return;
			}
		}
	}
	//try to stick it somewhere within the laid-out universe
	for(int x=minX; x<=maxX; ++x)
		for(int y=minY; y<=maxY; ++y){
			c->_x=x;
			c->_y=y;
			if(checkLayout(laidout)){
				c->noteLayout("within");
				return;
			}
		}
	//try to stick it above a connectee just beyond the universe
	for(auto& i: c->_connecters)
		if(i->_laidout){
			c->_x=maxX+1;
			c->_y=i->_y+1;
			if(checkLayout(laidout)){
				c->noteLayout("connecter-beyond");
				return;
			}
		}
	//try to stick it below a connectee just beyond the universe
	for(auto& i: c->_connections){
		auto j=i.second._component;
		if(j->_laidout){
			c->_x=maxX+1;
			c->_y=j->_y-1;
			if(checkLayout(laidout)){
				c->noteLayout("connectee-beyond");
				return;
			}
		}
	}
	//try to stick it just beyond the laid-out universe
	for(int x=minX; x<=maxX+1; ++x)
		for(int y=minY; y<=maxY+1; ++y){
			c->_x=x;
			c->_y=y;
			if(checkLayout(laidout)){
				c->noteLayout("beyond");
				return;
			}
		}
	//
	for(auto& i: components) std::cout<<i<<": "<<i->_x<<", "<<i->_y<<" "<<(i->_laidout?"laid out":"")<<"\n";
	throw std::logic_error("couldn't lay out component");
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

void Component::renderLines(sf::VertexArray& v){
	//self
	std::vector<sf::Vertex> u;
	sketch(u, "++-+--+-++", _x, _y, heat(colorComponent, _heat));
	_heat/=2.0f;
	stripToLines(u, v);
	switch(_type){
		case AUDIO    : sketch(u, "=++==--==+", _x, _y, colorComponent); break;
		case BUFFER   : sketch(u, "-<+<+>->"  , _x, _y, colorComponent); break;
		case COMMANDER: sketch(u, "--+++--+"  , _x, _y, colorComponent); break;
		case LINER    : sketch(u, "-=+="      , _x, _y, colorComponent); break;
		case MIDI     : sketch(u, "--=++-"    , _x, _y, colorComponent); break;
		case NETWORK  : sketch(u, "--++"      , _x, _y, colorComponent); break;
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
				if(dy-_y==V){//directly below
					u.push_back(vertex(_x    , dy-2*S, cn));//drop to just above destination
					u.push_back(vertex(dx    , dy-2*S, cn));//align horizontally
				}
				else{
					sf::Color cf=heat(colorForward, i.second._heat);
					u.push_back(vertex(_x-2*S, _y+2*S, cf));//diagonal
					u.push_back(vertex(_x-2*S, dy-3*S, cf));//drop to just above destination
					u.push_back(vertex(_x    , dy-2*S, cn));//diagonal
					u.push_back(vertex(dx    , dy-2*S, cn));//align horizontally
				}
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
	sf::VertexArray v(sf::Lines);
	for(auto& i: _nameToComponent) i.second->renderLines(v);
	wv.draw(v);
	for(auto& i: _nameToComponent) i.second->renderText(wv, _font);
}

void Viewer::layout(){
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
		auto size=grouping.at(0)._components.size();
		for(unsigned iComponent=0; iComponent<size; ++iComponent){
			bool done=false;
			for(int x=0; x<size&&!done; ++x)
				for(int y=0; y<size&&!done; ++y){
					for(auto& group: grouping){
						group._components.at(iComponent)->_x=x;
						group._components.at(iComponent)->_y=y;
						group._components.at(iComponent)->_laidout=true;
					}
					done=true;
					for(auto& group: grouping)
						if(!checkLayout(group._components)) done=false;
				}
			if(!done){
				printLayout();
				throw std::logic_error("couldn't lay out grouping");
			}
		}
		for(auto& group: grouping)
			for(auto & component: group._components)
				component->_laidout=false;
		for(auto& group: grouping){
			layout(group);
		}
	}
	//layout
	while(true){
		Component* component=NULL;
		auto unlaidout=OBVIOUS_TRANSFORM(_nameToComponent, if(!i->second->_laidout) r.push_back(i->second), std::vector<Component*>());
		if(unlaidout.empty()) break;
		//find a component to lay out
		if(!component) for(auto& i: unlaidout){//has laid-out connecter
			for(auto& j: i->_connecters) if(j->_laidout){ component=i; break; }
		}
		if(!component) for(auto& i: unlaidout){//has laid-out connectee
			for(auto& j: i->_connections) if(j.second._component->_laidout){ component=i; break; }
		}
		if(!component) component=unlaidout.front();//fallback
		//lay out
		layout(component);
	}
	//logical coordinates to pixels
	int minX=OBVIOUS_TRANSFORM(_nameToComponent, OBVIOUS_MIN(r, i->second->_x), 0);
	int minY=OBVIOUS_TRANSFORM(_nameToComponent, OBVIOUS_MIN(r, i->second->_y), 0);
	for(auto& i: _nameToComponent){
		i.second->_x=(i.second->_x-minX+1)*H;
		i.second->_y=(i.second->_y-minY+1)*V;
	}
}

void Viewer::layout(Group& g){
	int dX, dY;
	{
		int minX=OBVIOUS_TRANSFORM(g._components, OBVIOUS_MIN(r, (*i)->_x), 0);
		int minY=OBVIOUS_TRANSFORM(g._components, OBVIOUS_MIN(r, (*i)->_y), 0);
		int maxX=OBVIOUS_TRANSFORM(g._components, OBVIOUS_MAX(r, (*i)->_x), 0);
		int maxY=OBVIOUS_TRANSFORM(g._components, OBVIOUS_MAX(r, (*i)->_y), 0);
		dX=maxX-minX+1;
		dY=maxY-minY+1;
	}
	auto getComponents=[&](){
		return OBVIOUS_TRANSFORM(_nameToComponent, if(i->second->_laidout) r.push_back(i->second), std::vector<Component*>());
	};
	auto components=getComponents();
	int minX=OBVIOUS_TRANSFORM(components, OBVIOUS_MIN(r, (*i)->_x), 0);
	int minY=OBVIOUS_TRANSFORM(components, OBVIOUS_MIN(r, (*i)->_y), 0);
	int maxX=OBVIOUS_TRANSFORM(components, OBVIOUS_MAX(r, (*i)->_x), 0);
	int maxY=OBVIOUS_TRANSFORM(components, OBVIOUS_MAX(r, (*i)->_y), 0);
	for(auto& i: g._components) i->_laidout=true;
	components=getComponents();
	for(unsigned x=minX; x<=maxX+dX; x+=dX){
		for(auto& i: g._components) i->_x+=x;
		for(unsigned y=minY; y<=maxY+dY; y+=dY){
			for(auto& i: g._components) i->_y+=y;
			if(checkLayout(components)){
				for(auto& i: g._components) i->noteLayout("group");
				return;
			}
			for(auto& i: g._components) i->_y-=y;
		}
		for(auto& i: g._components) i->_x-=x;
	}
	printLayout();
	throw std::logic_error("couldn't lay out group");
}

void Viewer::layout(Component* c){
	auto x=OBVIOUS_TRANSFORM(_nameToComponent, r.push_back(i->second), std::vector<Component*>());
	::layout(c, x);
}
