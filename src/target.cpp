
#include "target.h"

#include <cstdint>

namespace liftover {

Target::Target(Tree::interval_vector ivals, bool _one_based) {
  one_based = _one_based;
  tree = Tree(std::move(ivals));
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
