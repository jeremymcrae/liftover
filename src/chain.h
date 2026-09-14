#ifndef LIFTOVER_CHAIN_H
#define LIFTOVER_CHAIN_H

#include <cstdint>
#include <vector>

#include "headers.h"
#include "intervaltree/IntervalTree.h"

namespace liftover {

struct Mapped {
  // holds where a liftover region maps across to
  std::int64_t start;
  std::string query_id;
  bool fwd_strand;
  std::int64_t size;
};

typedef IntervalTree<std::int64_t, Mapped> Tree;

class Chain {
  // class to hold all the regions for a single chain
  std::int64_t target = 0;
  std::int64_t query = 0;
  std::string query_id;
  std::string query_strand;
  std::int64_t query_size = 0;
  std::int64_t target_end = 0;
  std::int64_t query_end = 0;
  
  std::int64_t size = 0;
  std::int64_t target_gap = 0;
  std::int64_t query_gap = 0;
public:
  Tree::interval_vector intervals;
  std::string target_id;
  
  Chain() = default;
  Chain(std::string & header_line);
  void add_line(std::string & line);
  void validate();
  void save_to(Tree::interval_vector & dest);
};

} //namespace

#endif
