#include "filei.hpp"

DLAL_BUILD_COMPONENT_DEFINITION(Filei)

namespace dlal{

Filei::Filei(): _evaluation(0), _index(0) {
	addJoinAction([this](System&){
		if(!_file.is_open()&&_loaded.empty()) return "error: no file loaded!";
		for(auto page: _loaded)
			if(page._type==Page::AUDIO&&page._audio.size()!=_samplesPerEvaluation)
				return "error: samplesPerEvaluation and page audio size don't match";
		return "";
	});
	registerCommand("file_name", "<input file name>", [this](std::stringstream& ss){
		std::string fileName;
		ss>>fileName;
		std::ifstream file(fileName.c_str());
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
		std::string fileName;
		ss>>fileName;
		_file.open(fileName.c_str());
		if(!_file.is_open()) return "error: couldn't open file!";
		return "";
	});
}

void Filei::evaluate(){
	if(_file.is_open()){
		Page page(_file);
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
