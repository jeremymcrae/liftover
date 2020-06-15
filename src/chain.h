#ifndef LIFTOVER_CHAIN_H
#define LIFTOVER_CHAIN_H

#include <vector>
#include <sstream>

#include "headers.h"
// #include "utils.h"

namespace liftover {

struct Mapped {
  // holds where a liftover region maps across to
  long start;
  long stop;
  std::string query_id;
  bool fwd_strand;
  long size;
};

struct Coords {
  // store start and end coordinates, and where the region maps to
  long start;
  long end;
  Mapped data;
};

inline void parse(std::string & line, long * coords);

class Chain {
  // class to hold all the regions for a single chain
public:
  std::vector<Coords> intervals;
  std::string target_id;
  Chain(std::vector<std::string> & lines);
  Chain() {};
};


} //namespace

#endif
