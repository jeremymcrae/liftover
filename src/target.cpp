#include "target.h"

#include <algorithm>
#include <cstdint>

namespace liftover {

Target::Target(std::vector<Interval> ivals, bool _one_based)
  : intervals(std::move(ivals)), one_based(_one_based) {
  if (intervals.size() <= 1) {
    return;
  }

  bool sorted = true;
  bool has_overlaps = false;
  std::int64_t prev_start = intervals[0].start;
  std::int64_t max_stop = intervals[0].stop;
  for (std::size_t i = 1; i < intervals.size(); ++i) {
    if (intervals[i].start < prev_start) {
      sorted = false;
      break;
    }
    if (intervals[i].start < max_stop) {
      has_overlaps = true;
    }
    prev_start = intervals[i].start;
    if (intervals[i].stop > max_stop) {
      max_stop = intervals[i].stop;
    }
  }

  if (!sorted) {
    std::sort(intervals.begin(), intervals.end(),
              [](const Interval & a, const Interval & b) {
                return a.start != b.start ? a.start < b.start : a.stop < b.stop;
              });
    has_overlaps = false;
    max_stop = intervals[0].stop;
    for (std::size_t i = 1; i < intervals.size(); ++i) {
      if (intervals[i].start < max_stop) {
        has_overlaps = true;
        break;
      }
      if (intervals[i].stop > max_stop) {
        max_stop = intervals[i].stop;
      }
    }
  }

  if (has_overlaps) {
    max_stops.resize(intervals.size());
    build_max_stops(0, intervals.size());
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
  const Mapped & mapped = region.value;
  std::int64_t offset = pos - region.start;
  std::int64_t remapped = mapped.fwd_strand ? mapped.start + offset : mapped.start - offset;
  if (one_based) {
    remapped += 1;
  }
  return Match {remapped, mapped.query_id_idx, mapped.fwd_strand};
}

void Target::query_overlapping(std::size_t low, std::size_t high, std::int64_t pos, MatchBuffer & matches) const {
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

void Target::query(std::int64_t pos, MatchBuffer & matches) const {
  /* find coordinates matching a specific site without heap allocation for <= 4 hits
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
