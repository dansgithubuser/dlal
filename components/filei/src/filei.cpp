#include "filei.hpp"

void* dlalBuildComponent(){ return (dlal::Component*)new dlal::Filei; }

namespace dlal{

Filei::Filei(): _evaluation(0), _index(0) {
	addJoinAction([this](System&){
		if(_loaded.empty()) return "error: no file loaded!";
		for(auto page: _loaded)
			if(page._type==Page::AUDIO&&page._audio.size()!=_samplesPerEvaluation)
				return "error: samplesPerEvaluation and page audio size don't match";
		return "";
	});
	registerCommand("name", "<input file name>", [this](std::stringstream& ss){
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
}

void Filei::evaluate(){
	while(_index<_loaded.size()){
		Page& page=_loaded[_index];
		if(page._evaluation>_evaluation) break;
		page.dispatch(_samplesPerEvaluation, _outputs);
		++_index;
	}
	++_evaluation;
}

}//namespace dlal
