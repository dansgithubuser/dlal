#include "filei.hpp"

DLAL_BUILD_COMPONENT_DEFINITION(Filei)

namespace dlal{

Filei::Filei(): _evaluation(0), _index(0), _queue(8) {
	addJoinAction([this](System&){
		if(!_file.is_open()&&_loaded.empty()) return "error: no file loaded!";
		for(auto page: _loaded)
			if(page._type==Page::AUDIO&&page._audio.size()!=_samplesPerEvaluation)
				return "error: samplesPerEvaluation and page audio size don't match";
		return "";
	});
	registerCommand("file_name", "<input file name>", [this](std::stringstream& ss){
		ss>>_fileName;
		std::ifstream file(_fileName.c_str());
		if(!file.is_open()) return "error: couldn't open file!";
		_loaded.clear();
		while(true){
			Page page(file);
			if(!file.good()) break;
			_loaded.push_back(page);
		}
		if(!_loaded.size()) return "error: file is empty!";
		return "";
	});
	registerCommand("stream", "<input file name>", [this](std::stringstream& ss){
		ss>>_fileName;
		_file.open(_fileName.c_str());
		if(!_file.is_open()) return "error: couldn't open file!";
		_thread=std::thread([this](){
			while(!_quit){
				while(_queue.readSize()<128){
					auto position=_file.tellg();
					Page page(_file);
					if(page){
						if(_file.tellg()==-1){
							_file=std::ifstream(_fileName.c_str());
							_file.seekg(position);
							break;
						}
						_queue.write(page);
					}
					else{
						_file=std::ifstream(_fileName.c_str());
						_file.seekg(position);
						break;
					}
				}
				std::this_thread::sleep_for(std::chrono::milliseconds(1));
			}
		});
		return "";
	});
}

Filei::~Filei(){
	_quit=true;
	if(_thread.joinable()) _thread.join();
}

void Filei::evaluate(){
	if(_queue.readSize()){
		Page page;
		_queue.read(page, true);
		page.dispatch(*this, _outputs, _samplesPerEvaluation);
	}
	else while(_index<_loaded.size()){
		Page& page=_loaded[_index];
		if(page._evaluation>_evaluation) break;
		page.dispatch(*this, _outputs, _samplesPerEvaluation);
		++_index;
	}
	++_evaluation;
}

}//namespace dlal
