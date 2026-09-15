#ifndef LIFTOVER_CHAINFILE_H
#define LIFTOVER_CHAINFILE_H

#include <vector>
#include <string>
#include <map>

#include "chain.h"
#include "target.h"

namespace liftover {

struct ChainFileResult {
  std::map<std::string, Target> targets;
  std::vector<std::string> query_names;
};

ChainFileResult open_chainfile(std::string path, bool one_based=false);

}

#endif
