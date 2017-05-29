#include <SFML/Graphics.hpp>

#include <string>
#include <set>
#include <list>
#include <map>
#include <vector>
#include <iostream>

class Component{
	public:
		enum Type{
			OTHER,
			AUDIO,
			BUFFER,
			COMMANDER,
			LINER,
			MIDI,
			NETWORK
		};
		struct Connection{
			Connection(){}
			Connection(Component* component): _component(component), _on(true), _heat(0.0f) {}
			bool operator==(Connection& other) const{ return _component==other._component; }
			Component* _component;
			bool _on;
			float _heat;
		};
		Component();
		Component(std::string name, std::string type);
		void renderLines(sf::VertexArray&);
		void renderText(sf::RenderWindow&, const sf::Font&);
		void noteLayout(std::string method);
		std::string _name, _label;
		Type _type;
		float _phase, _heat;
		std::map<std::string, Connection> _connections;
		std::set<Component*> _connecters;
		int _x, _y;
		bool _laidout;
};

class Group{
	public:
		friend std::ostream& operator<<(std::ostream&, const Group&);
		Group(Component*);
		Group(const std::map<std::string, Component::Connection>&);
		Group(const std::set<Component*>&);
		bool operator<(const Group&) const;
		bool similar(const Group&) const;
		bool adjacent(const Group&) const;
		void merge(const Group&);
		std::vector<Component*> _components;
	private:
		void sort();
};

class Viewer{
	public:
		Viewer();
		void printLayout() const;
		void process(std::string);
		void render(sf::RenderWindow& windowVis, sf::RenderWindow& windowTxt);
	private:
		void layout();
		void layout(Group&);
		void layout(Component*);
		sf::Font _font;
		std::list<std::string> _reports;
		std::map<std::string, Component*> _nameToComponent;
		std::vector<std::pair<std::string, std::string>> _pendingConnections;
		std::map<std::string, std::string> _variables;
		unsigned _w, _h;
};
