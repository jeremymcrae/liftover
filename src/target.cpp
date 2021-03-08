
#include "target.h"

namespace liftover {

Target::Target(std::vector<Chain> & chains) {
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
  tree = Tree(std::move(intervals));
}

std::vector<Match> Target::query(long pos) {
  /* find coordinates matching a specific site
  */
  auto matched = tree.findOverlapping(pos, pos);
  std::vector<Match> matches(matched.size());
  for (uint i=0; i<matched.size(); i++) {
    auto & region = matched[i];
    if (pos == region.stop) {
      continue;
    }
    Mapped & mapped = region.value;
    long offset = pos - region.start;
    long remapped = mapped.start + offset;
    if (!mapped.fwd_strand) {
      remapped = mapped.size - remapped - 1;
    }
    matches[i] = Match {mapped.query_id, remapped, mapped.fwd_strand};
  }
  return matches;
}

} //namespace
