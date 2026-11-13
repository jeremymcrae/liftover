#ifndef LIFTOVER_CHAINFILE_H
#define LIFTOVER_CHAINFILE_H

#include <vector>
#include <string>
#include <map>

#include "chain.h"
#include "target.h"

namespace liftover {

// Indexed target chromosomes paired with the interned table of query contig names.
struct ChainFileResult {
  std::map<std::string, Target> targets;
  std::vector<std::string> query_names;
};

// Parse a gzip-compressed or plain chain file from an open file descriptor.
// Takes ownership of fd (setting fd = -1) once gzdopen succeeds.
ChainFileResult open_chainfile(int & fd, const std::string & path, bool one_based=false);

}

#endif
