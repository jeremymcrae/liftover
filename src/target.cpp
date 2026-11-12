
#include "target.h"

#include <cstdint>

namespace liftover {

Target::Target(Tree::interval_vector ivals, bool _one_based) {
  one_based = _one_based;
  tree = Tree(std::move(ivals));
}

void Target::query(std::int64_t pos, MatchBuffer & matches) const {
  /* find coordinates matching a specific site without heap allocation for <= 4 hits
  */
  matches.clear();

  // if lifting one-based coordinates, shift the pos to lift to zero-based
  if (one_based) {
    pos -= 1;
  }
  
  tree.visit_overlapping(pos, [&](const Tree::interval & region) {
    if (pos == region.stop) {
      return;
    }
    const Mapped & mapped = region.value;
    std::int64_t offset = pos - region.start;
    std::int64_t remapped = mapped.fwd_strand ? mapped.start + offset : mapped.start - offset;
    // if lifting one-based coordinates, shift the lifted position to one-based
    if (one_based) {
      remapped += 1;
    }
    
    matches.push_back(Match {remapped, mapped.query_id_idx, mapped.fwd_strand});
  });
}

std::vector<Match> Target::query(std::int64_t pos) const {
  MatchBuffer buf;
  query(pos, buf);
  std::vector<Match> matches;
  if (!buf.empty()) {
    matches.reserve(buf.size());
    for (std::size_t i = 0; i < buf.size(); ++i) {
      matches.push_back(buf[i]);
    }
  }
  return matches;
}

} //namespace
