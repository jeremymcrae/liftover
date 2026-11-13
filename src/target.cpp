#include "target.h"

#include <algorithm>
#include <cstdint>

namespace liftover {

Target::Target(std::vector<Interval> ivals, bool _one_based)
  : intervals(std::move(ivals)), one_based(_one_based) {
  if (intervals.size() <= 1) {
    return;
  }

  auto by_start = [](const Interval & a, const Interval & b) {
    return a.start < b.start;
  };
  if (!std::is_sorted(intervals.begin(), intervals.end(), by_start)) {
    std::sort(intervals.begin(), intervals.end(),
              [](const Interval & a, const Interval & b) {
                return a.start != b.start ? a.start < b.start : a.stop < b.stop;
              });
  }

  std::int64_t max_stop = intervals[0].stop;
  for (std::size_t i = 1; i < intervals.size(); ++i) {
    if (intervals[i].start < max_stop) {
      max_stops.resize(intervals.size());
      build_max_stops(0, intervals.size());
      break;
    }
    if (intervals[i].stop > max_stop) {
      max_stop = intervals[i].stop;
    }
  }
}

std::int64_t Target::build_max_stops(std::size_t low, std::size_t high) {
  std::size_t mid = low + (high - low) / 2;
  std::int64_t m = intervals[mid].stop;
  if (low < mid) {
    m = std::max(m, build_max_stops(low, mid));
  }
  if (mid + 1 < high) {
    m = std::max(m, build_max_stops(mid + 1, high));
  }
  max_stops[mid] = m;
  return m;
}

inline Match Target::remap(const Interval & region, std::int64_t pos) const {
  std::int64_t offset = pos - region.start;
  std::int64_t remapped = region.fwd_strand ? region.mapped_start + offset : region.mapped_start - offset;
  if (one_based) {
    remapped += 1;
  }
  return Match {remapped, region.query_id_idx, region.fwd_strand};
}

void Target::query_overlapping(std::size_t low, std::size_t high, std::int64_t pos, std::vector<Match> & matches) const {
  std::size_t mid = low + (high - low) / 2;
  if (pos >= max_stops[mid]) {
    return;
  }
  if (low < mid) {
    query_overlapping(low, mid, pos, matches);
  }
  const Interval & region = intervals[mid];
  if (pos < region.start) {
    return;
  }
  if (pos < region.stop) {
    matches.push_back(remap(region, pos));
  }
  if (mid + 1 < high) {
    query_overlapping(mid + 1, high, pos, matches);
  }
}

void Target::query(std::int64_t pos, std::vector<Match> & matches) const {
  /* find coordinates matching a specific site, reusing the caller's vector capacity
  */
  matches.clear();

  if (one_based) {
    if (pos < 1) {
      return;
    }
    pos -= 1;
  } else if (pos < 0) {
    return;
  }

  if (intervals.empty() || pos < intervals.front().start) {
    return;
  }

  if (max_stops.empty()) {
    auto it = std::upper_bound(
      intervals.begin(), intervals.end(), pos,
      [](std::int64_t p, const Interval & iv) { return p < iv.start; });
    --it;
    if (pos < it->stop) {
      matches.push_back(remap(*it, pos));
    }
    return;
  }

  query_overlapping(0, intervals.size(), pos, matches);
}

} //namespace
