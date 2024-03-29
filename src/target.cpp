
#include "target.h"

#include <cstdint>
#include <iostream>

namespace liftover {

Target::Target(std::vector<Chain> & chains, bool _one_based) {
  /* make set of targets for a single chromosome
  
  This uses a vector of chains, all for a given chromosome, and builds an
  intervaltree for later querying of coordinates.
  */
  target_id = chains[0].target_id;
  Tree::interval_vector intervals;
  
  int size = 0;
  for (auto chain : chains) { size += chain.intervals.size(); }
  intervals.reserve(size);
  
  // make intervals for the tree from all regions in all chains
  for (auto chain : chains) {
    for (auto ival: chain.intervals) {
      intervals.push_back(Tree::interval(ival.start, ival.end, ival.data));
    }
    assert(target_id == chain.target_id);
  }
  one_based = _one_based;
  tree = Tree(std::move(intervals));
}

std::vector<Match> Target::query(std::int64_t pos) {
  /* find coordinates matching a specific site
  */
  // if lifting one-based coordinates, shift the pos to lift to zero-based
  pos -= (std::uint64_t) one_based;
  
  std::vector<Match> matches;
  matches.reserve(1);
  for (auto & region : tree.findOverlapping(pos, pos)) {
    if (pos == region.stop) {
      continue;
    }
    Mapped & mapped = region.value;
    std::int64_t offset = pos - region.start;
    std::int64_t remapped = mapped.start + offset;
    if (!mapped.fwd_strand) {
      remapped = mapped.size - remapped - 1;
    }
    // if lifting one-based coordinates, shift the lifted position to one-based
    remapped += (std::uint64_t) one_based;
    
    matches.push_back( Match {mapped.query_id, remapped, mapped.fwd_strand});
  }
  return matches;
}

} //namespace
