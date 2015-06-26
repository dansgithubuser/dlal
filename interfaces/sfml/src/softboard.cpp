#include "softboard.hpp"

#include <page.hpp>

#include <sstream>

Softboard::Softboard(): _octave(0) {}

std::string Softboard::processKey(sf::Keyboard::Key key, bool on){
	uint8_t note;
	switch(key){
		case sf::Keyboard::Key::Z:     note=0x30; break;
		case sf::Keyboard::Key::S:     note=0x31; break;
		case sf::Keyboard::Key::X:     note=0x32; break;
		case sf::Keyboard::Key::D:     note=0x33; break;
		case sf::Keyboard::Key::C:     note=0x34; break;
		case sf::Keyboard::Key::V:     note=0x35; break;
		case sf::Keyboard::Key::G:     note=0x36; break;
		case sf::Keyboard::Key::B:     note=0x37; break;
		case sf::Keyboard::Key::H:     note=0x38; break;
		case sf::Keyboard::Key::N:     note=0x39; break;
		case sf::Keyboard::Key::J:     note=0x3a; break;
		case sf::Keyboard::Key::M:     note=0x3b; break;
		case sf::Keyboard::Key::Comma: note=0x3c; break;

		case sf::Keyboard::Key::W:     note=0x3c; break;
		case sf::Keyboard::Key::Num3:  note=0x3d; break;
		case sf::Keyboard::Key::E:     note=0x3e; break;
		case sf::Keyboard::Key::Num4:  note=0x3f; break;
		case sf::Keyboard::Key::R:     note=0x40; break;
		case sf::Keyboard::Key::T:     note=0x41; break;
		case sf::Keyboard::Key::Num6:  note=0x42; break;
		case sf::Keyboard::Key::Y:     note=0x43; break;
		case sf::Keyboard::Key::Num7:  note=0x44; break;
		case sf::Keyboard::Key::U:     note=0x45; break;
		case sf::Keyboard::Key::Num8:  note=0x46; break;
		case sf::Keyboard::Key::I:     note=0x47; break;
		case sf::Keyboard::Key::O:     note=0x48; break;

		case sf::Keyboard::Key::Up:   if(on) ++_octave; return "";
		case sf::Keyboard::Key::Down: if(on) --_octave; return "";

		default: return "";
	}
	dlal::MidiMessage message;
	message._bytes[0]=on?0x90:0x80;
	message._bytes[1]=12*_octave+note;
	message._bytes[2]=0x3f;
	dlal::MidiMessages messages(message);
	dlal::Page page;
	page.fromMidi(&messages, 0);
	std::stringstream ss;
	page.toFile(ss);
	return ss.str();
}