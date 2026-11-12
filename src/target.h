#ifndef LIFTOVER_TARGET_H
#define LIFTOVER_TARGET_H

#include <cstdint>
#include <utility>
#include <vector>

#include "chain.h"

namespace liftover {

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
  /* indexes the intervals for a single chromosome for fast point queries.

  Intervals are stored in a flat vector sorted by start coordinate. When no
  intervals on the chromosome overlap (true for all UCSC over.chain contigs),
  queries run a single std::upper_bound binary search. When intervals overlap,
  max_stops augments the array as an implicit midpoint interval tree.
  */
  std::vector<Interval> intervals;
  std::vector<std::int64_t> max_stops;
  bool one_based = false;

  std::int64_t build_max_stops(std::size_t low, std::size_t high);
  void query_overlapping(std::size_t low, std::size_t high, std::int64_t pos, MatchBuffer & matches) const;
  Match remap(const Interval & region, std::int64_t pos) const;
public:
  Target(std::vector<Interval> ivals, bool _one_based = false);
  Target() = default;
  Target(Target&&) = default;
  Target& operator=(Target&&) = default;
  Target(const Target&) = default;
  Target& operator=(const Target&) = default;
  void swap(Target & other) noexcept {
    intervals.swap(other.intervals);
    max_stops.swap(other.max_stops);
    std::swap(one_based, other.one_based);
  }
  void query(std::int64_t pos, MatchBuffer & matches) const;
  std::vector<Match> query(std::int64_t pos) const;
  std::vector<Match> operator[](std::int64_t pos) const { return query(pos); }
};

} //namespace

#endif
