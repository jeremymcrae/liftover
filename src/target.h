#ifndef LIFTOVER_TARGET_H
#define LIFTOVER_TARGET_H

#include <cstdint>
#include <vector>

#include "headers.h"
#include "chain.h"

#include "intervaltree/IntervalTree.h"

namespace liftover {

typedef IntervalTree<std::int64_t, Mapped> Tree;

struct Match {
  // hold info for a matched site after a successful query
  std::string contig;
  std::int64_t pos;
  bool fwd_strand;
};

class Target {
  /* converts the vector of chains for a single chromosome for quick queries
  
  Objects of this type are stored inside a map, indexed by chromosome, so this
  just has to handle nucleotide position queries. Ideally the interface should
  work like: map[chrom][pos]
  
  Currently stores the regions in an interval tree for fast queries.
  */
 bool one_based=false;
  Tree tree;
  std::string target_id;
public:
  Target(std::vector<Chain> & chains, bool _one_based=false);
  Target() {}
  std::vector<Match> query(std::int64_t pos);
  std::vector<Match> operator[](std::int64_t pos) {return query(pos);}
};

} //namespace

#endif
