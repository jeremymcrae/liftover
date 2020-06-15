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
  long target;
  long query;
  std::string query_id;
  std::string query_strand;
  long query_size;
  long target_end;
  long query_end;
  
  long size;
  long target_gap;
  long query_gap;
public:
  std::vector<Coords> intervals;
  std::string target_id;
  
  Chain() {};
  Chain(std::string & header_line);
  void add_line(std::string & line);
};


} //namespace

#endif
