#include <SFML/Window.hpp>

#include <string>

class Softboard{
	public:
		Softboard();
		std::string processKey(sf::Keyboard::Key key, bool on);
	private:
		int _octave;
};
