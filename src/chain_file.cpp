
#include "chain_file.h"

namespace liftover {

std::map<std::string, Target> open_chainfile(std::string path) {
  /* open a gzipped liftover chain file, and parses contents
  
  This builds a map of Targets, indexed by chromosome, so we can quickly select
  the Target of interest when querying a given coordinate.
  */
  igzstream infile(path.c_str());
  std::string line;
  std::map<std::string, std::vector<Chain>> chains;
  Chain chain;
  while (std::getline(infile, line)) {
    if (line[0] == '#') { continue; } // skip comment lines
    
    if (line.substr(0, 5) == "chain") {
      chain = Chain(line);
    } else if (line.empty()) { // finish existing chain at blank lines
      chains[chain.target_id].push_back(chain);
    } else {
      chain.add_line(line);
    }
  }
  
  // convert list of intervals into interval trees for each chromosome
  std::map<std::string, Target> targets;
  for (auto x : chains) {
    targets[x.first] = Target(x.second);
  }
  return targets;
}

} //namespace
