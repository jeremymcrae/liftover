#ifndef LIFTOVER_CHAIN_H
#define LIFTOVER_CHAIN_H

#include <cstdint>
#include <vector>
#include <sstream>

#include "headers.h"
// #include "utils.h"

namespace liftover {

struct Mapped {
  // holds where a liftover region maps across to
  std::int64_t start;
  std::int64_t stop;
  std::string query_id;
  bool fwd_strand;
  std::int64_t size;
};

struct Coords {
  // store start and end coordinates, and where the region maps to
  std::int64_t start;
  std::int64_t end;
  Mapped data;
};

inline void parse(std::string & line, std::int64_t * coords);

class Chain {
  // class to hold all the regions for a single chain
  std::int64_t target;
  std::int64_t query;
  std::string query_id;
  std::string query_strand;
  std::int64_t query_size;
  std::int64_t target_end;
  std::int64_t query_end;
  
  std::int64_t size;
  std::int64_t target_gap;
  std::int64_t query_gap;
public:
  std::vector<Coords> intervals;
  std::string target_id;
  
  Chain() {}
  Chain(std::string & header_line);
  void add_line(std::string & line);
};


} //namespace

#endif
