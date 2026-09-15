
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
  if (one_based) {
    pos -= 1;
  }
  
  std::vector<Match> matches;
  matches.reserve(1);
  tree.visit_overlapping(pos, [&](const Tree::interval & region) {
    if (pos == region.stop) {
      return;
    }
    const Mapped & mapped = region.value;
    std::int64_t offset = pos - region.start;
    std::int64_t remapped = mapped.start + offset;
    if (!mapped.fwd_strand) {
      remapped = mapped.size - remapped - 1;
    }
    // if lifting one-based coordinates, shift the lifted position to one-based
    if (one_based) {
      remapped += 1;
    }
    
    matches.push_back(Match {mapped.query_id_idx, remapped, mapped.fwd_strand});
  });
  return matches;
}

} //namespace
