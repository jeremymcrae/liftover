
#include <stdexcept>

#include "chain_file.h"

namespace liftover {

std::map<std::string, Target> open_chainfile(std::string path, bool one_based) {
  /* open a gzipped liftover chain file, and parses contents
  
  This builds a map of Targets, indexed by chromosome, so we can quickly select
  the Target of interest when querying a given coordinate.
  */
  igzstream infile(path.c_str());
  if (!infile.good()) {
    throw std::invalid_argument("cannot open chain file at " + path);
  }

  std::string line;
  std::map<std::string, std::vector<Chain>> chains;
  Chain chain;
  bool has_chain = false;
  while (std::getline(infile, line)) {
    // sanatize line endings
    if (!line.empty() && line.back() == '\r') {
      line.pop_back();
    }
    
    if (line.empty()) {
      // finish existing chain at blank lines
      if (has_chain) {
        chain.validate();
        chains[chain.target_id].push_back(chain);
        has_chain = false;
      }
    } else if (line[0] == '#') {
      // skip comment lines
      continue;
    } else if (line.substr(0, 5) == "chain") {
      chain = Chain(line);
      has_chain = true;
    } else {
      chain.add_line(line);
    }
  }

  if (has_chain) {
    // include the final chain, if the file doesn't end with a blank line
    chain.validate();
    chains[chain.target_id].push_back(chain);
  }
  
  // convert list of intervals into interval trees for each chromosome
  std::map<std::string, Target> targets;
  for (auto & x : chains) {
    targets[x.first] = Target(x.second, one_based);
  }
  return targets;
}

} //namespace
