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
  void query_overlapping(std::size_t low, std::size_t high, std::int64_t pos, std::vector<Match> & matches) const;
  Match remap(const Interval & region, std::int64_t pos) const;
public:
  Target(std::vector<Interval> ivals, bool _one_based = false);
  Target() = default;
  void swap(Target & other) noexcept {
    intervals.swap(other.intervals);
    max_stops.swap(other.max_stops);
    std::swap(one_based, other.one_based);
  }
  void query(std::int64_t pos, std::vector<Match> & matches) const;
};

} //namespace

#endif
