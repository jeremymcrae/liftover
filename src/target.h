#ifndef LIFTOVER_TARGET_H
#define LIFTOVER_TARGET_H

#include <cstdint>
#include <utility>
#include <vector>

#include "chain.h"

namespace liftover {

// Lifted query coordinate for a single matching chain interval.
struct Match {
  std::int64_t pos;
  std::uint32_t query_id_idx;
  bool fwd_strand;
};

// Per-chromosome interval index for fast point coordinate queries.
// Intervals are sorted by start coordinate: disjoint contigs (all UCSC over.chain
// contigs) use a single binary search, while contigs with overlapping chains also
// populate max_stops as an implicit augmented binary search tree.
class Target {
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
