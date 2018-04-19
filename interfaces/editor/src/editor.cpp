#include "component.hpp"
#include "connection.hpp"
#include "variable.hpp"

#include <dryad.hpp>
#include <page.hpp>
#include <wrapper.hpp>

#include <fstream>
#include <map>
#include <string>

template<typename K, typename V> struct DeleterMap: public std::map<K, V> {
	~DeleterMap(){ for(auto i: *this) delete i.second; }
};

dryad::Client* fClient=nullptr;
std::string fString;
std::string fText;
std::map<std::string, Variable> fVariables;
std::map<std::string, Component> fComponents;
std::vector<Object*> fSelected;
DeleterMap<std::string, dryad::Client*> fTies;
std::vector<Component> fAddables;
int fAddablesScrollX=0, fAddablesScrollY=0;

extern "C" {
	void editor_init(const char* host, int port, const char* componentTypes){
		fClient=new dryad::Client(host, port);
		std::stringstream ss(componentTypes);
		std::string componentType;
		int y=SZ;
		while(ss>>componentType){
			fAddables.push_back(Component().set("", componentType, -ADDABLES_WIDTH, y, &fAddablesScrollX, &fAddablesScrollY));
			y+=4*SZ;
		}
	}

	void editor_finish(){
		delete fClient;
	}

	const char* editor_dryad_read(){
		if(!fClient) return nullptr;
		return fClient->readSizedString(fString)?fString.c_str():"";
	}

	int editor_dryad_times_connected(){
		if(!fClient) return -1;
		return fClient->timesConnected();
	}

	int editor_dryad_times_disconnected(){
		if(!fClient) return -1;
		return fClient->timesDisconnected();
	}

	void editor_set_text(const char* s){
		fText=s;
	}

	void editor_draw(){
		//clear
		gDansSfmlWrapperBoss->window.clear();
		//objects
		static sf::VertexArray va(sf::PrimitiveType::Lines);
		for(auto& i: fComponents) i.second.draw(va, in((Object*)&i.second, fSelected));
		//objects - addables
		fAddablesScrollX=dans_sfml_wrapper_width();
		for(auto& i: fAddables) i.draw(va, false, true);
		//objects - draw
		gDansSfmlWrapperBoss->window.draw(va, sf::RenderStates(sf::BlendMode(
			sf::BlendMode::Factor::One, sf::BlendMode::Factor::OneMinusSrcAlpha
		)));
		va.clear();
		//variables
		for(const auto& i: fVariables) i.second.draw(in((Object*)&i.second, fSelected));
		//text
		dans_sfml_wrapper_text_draw(SZ, gDansSfmlWrapperBoss->window.getSize().y-SZ, SZ, fText.c_str(), 255, 255, 255, 255);
		//display
		gDansSfmlWrapperBoss->window.display();
	}

	void editor_push(const char* command){
		if(!fClient) throw std::logic_error("not initialized");
		Component* component=nullptr;
		for(auto& i: fComponents) if(
			i.second._type=="network"&&
			i.second._connections.size()==1&&
			i.second._connections.begin()->second._dst->_type=="commander"&&
			i.second._connections.begin()->second._dst->_connections.size()==0
		){
			component=&i.second;
			break;
		}
		std::stringstream ss;
		dlal::Page(command, 0).toFile(ss);
		if(component){
			auto name=component->_name;
			if(!fTies.count(name))
				fTies[name]=new dryad::Client(fClient->ip(), std::stoi(fVariables.at(name+".port")._value));
			fTies.at(name)->writeSizedString(ss.str());
		}
		else fClient->writeSizedString(ss.str());
	}

	void editor_save(const char* fileName){
		typedef CartesianPair<int> Pair;
		typedef std::map<std::string, Pair> Map;
		std::ofstream(fileName)
			<<OBV_FOR(fVariables , r[i->first]=Pair(i->second._x, i->second._y), Map())
			<<OBV_FOR(fComponents, r[i->first]=Pair(i->second._x, i->second._y), Map())
		;
	}

	void editor_load(const char* fileName){
		std::map<std::string, CartesianPair<int>> vPairs, cPairs;
		std::ifstream(fileName)>>vPairs>>cPairs;
		for(auto& i: vPairs)
			fVariables [i.first].name(i.first).moveTo(i.second.x, i.second.y);
		for(auto& i: cPairs)
			fComponents[i.first].name(i.first).moveTo(i.second.x, i.second.y);
	}

	void editor_name(){
		for(auto& i: fSelected){
			auto component=dynamic_cast<Component*>(i);
			if(!component) continue;
			component->name();
		}
	}

	int addables_width(){ return ADDABLES_WIDTH; }

	void* addable_at(int x, int y){
		for(auto& i: fAddables) if(i.contains(x, y)) return &i;
		return nullptr;
	}

	void addables_scroll(int dy){
		fAddablesScrollY+=dy;
	}

	void* object_at(int x, int y){
		std::vector<Object*> objects;
		for(auto& i: fComponents) objects.push_back(&i.second);
		for(auto& i: fVariables) objects.push_back(&i.second);
		for(auto& i: objects) if(i->contains(x, y)) return i;
		return nullptr;
	}

	void object_move_by(Object* object, int dx, int dy){
		object->moveBy(dx, dy);
	}

	void selection_add(Object* object){
		if(!in(object, fSelected)) fSelected.push_back(object);
	}

	void selection_clear(){ fSelected.clear(); }

	int selection_size(){ return fSelected.size(); }

	void* selection_at_index(int i){ return fSelected.at(i); }

	void* selection_component(){
		if(fSelected.size()!=1) return nullptr;
		auto result=fSelected.at(0);
		if(!dynamic_cast<Component*>(result)) return nullptr;
		return result;
	}

	void variable_set(const char* name, const char* value){
		if(fVariables.count(name)) fVariables.at(name)._value=value;
		else fVariables[name]
			.name(name)
			.value(value)
			.moveTo(400, SZ*fVariables.size());
	}

	void component_new(const char* name, const char* type, int x, int y){
		if(fComponents.count(name)) fComponents.at(name)._type=type;//component was previously loaded
		else fComponents[name].set(name, type, x, y);
	}

	void component_label(const char* name, const char* label){
		fComponents[name]._label=label;
	}

	void component_phase(const char* name, float phase){
		if(!fComponents.count(name)) return;
		fComponents.at(name)._phase=phase;
	}

	const char* component_type(Object* component){
		return dynamic_cast<Component*>(component)->_type.c_str();
	}

	const char* component_name(Object* component){
		return dynamic_cast<Component*>(component)->_name.c_str();
	}

	void connection_new(const char* src, const char* dst){
		fComponents[src];
		fComponents[dst];
		fComponents.at(src)._connections[dst]=Connection(&fComponents.at(src), &fComponents.at(dst));
	}

	void connection_del(const char* src, const char* dst){
		if(!fComponents.count(src)) return;
		eraseKey(dst, fComponents.at(src)._connections);
	}

	void connection_command(const char* src, const char* dst){
		if(!fComponents.count(src)) return;
		if(!fComponents.at(src)._connections.count(dst)) return;
		fComponents.at(src)._connections.at(dst)._commandHeat=1.0f;
	}

	void connection_midi(const char* src, const char* dst){
		if(!fComponents.count(src)) return;
		if(!fComponents.at(src)._connections.count(dst)) return;
		fComponents.at(src)._connections.at(dst)._midiHeat=1.0f;
	}

	void connection_toggle(Object* connectorObject, Object* connecteeObject){
		Component* connector=dynamic_cast<Component*>(connectorObject);
		Component* connectee=dynamic_cast<Component*>(connecteeObject);
		bool connected=false;
		for(auto& i: connector->_connections)
			if(i.second._dst==connectee){
				connected=true;
				break;
			}
		editor_push(obvstr(
			connected?"queue_disconnect":"queue_connect",
			connector->_name,
			connectee->_name
		).c_str());
	}
}
