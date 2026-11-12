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
  std::int64_t pos;
  std::uint32_t query_id_idx;
  bool fwd_strand;
};

struct MatchBuffer {
  // stack-friendly buffer avoiding heap allocation for typical (<= 4) matches
  enum : std::size_t { INLINE_CAP = 4 };
  Match inline_matches[INLINE_CAP];
  std::vector<Match> extra;
  std::size_t count = 0;

  void clear() {
    count = 0;
    if (!extra.empty()) {
      extra.clear();
    }
  }

  void push_back(const Match & m) {
    if (count < INLINE_CAP) {
      inline_matches[count] = m;
    } else {
      extra.push_back(m);
    }
    ++count;
  }

  std::size_t size() const { return count; }
  bool empty() const { return count == 0; }

  const Match & operator[](std::size_t i) const {
    return i < INLINE_CAP ? inline_matches[i] : extra[i - INLINE_CAP];
  }
};

class Target {
  /* converts the vector of chains for a single chromosome for quick queries
  
  Objects of this type are stored inside a map, indexed by chromosome, so this
  just has to handle nucleotide position queries. Ideally the interface should
  work like: map[chrom][pos]
  
  Currently stores the regions in an interval tree for fast queries.
  */
  bool one_based = false;
  Tree tree;
public:
  Target(Tree::interval_vector ivals, bool _one_based = false);
  Target() = default;
  Target(Target&&) = default;
  Target& operator=(Target&&) = default;
  Target(const Target&) = default;
  Target& operator=(const Target&) = default;
  void swap(Target & other) noexcept {
    std::swap(one_based, other.one_based);
    std::swap(tree, other.tree);
  }
  void query(std::int64_t pos, MatchBuffer & matches) const;
  std::vector<Match> query(std::int64_t pos) const;
  std::vector<Match> operator[](std::int64_t pos) const { return query(pos); }
};

} //namespace

#endif
