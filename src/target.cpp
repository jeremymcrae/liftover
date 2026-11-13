#include "target.h"

#include <algorithm>
#include <cstdint>

namespace liftover {

Target::Target(std::vector<Interval> ivals, bool _one_based)
  : intervals(std::move(ivals)), one_based(_one_based) {
  if (intervals.size() <= 1) {
    return;
  }

  // Sort intervals by start coordinate when multiple chains on a chromosome are unordered.
  auto by_start = [](const Interval & a, const Interval & b) {
    return a.start < b.start;
  };
  if (!std::is_sorted(intervals.begin(), intervals.end(), by_start)) {
    std::stable_sort(intervals.begin(), intervals.end(), by_start);
  }

  // Only build the augmented max_stops tree if at least two intervals overlap;
  // otherwise query() can answer lookups with a single upper_bound binary search.
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

// Populate max_stops[mid] with the maximum stop coordinate across intervals[low..high),
// turning the sorted array into an implicit balanced augmented interval tree.
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

// Convert a 0-based target position falling within region into its query coordinate.
inline Match Target::remap(const Interval & region, std::int64_t pos) const {
  std::int64_t offset = pos - region.start;
  std::int64_t remapped = region.fwd_strand ? region.mapped_start + offset : region.mapped_start - offset;
  if (one_based) {
    remapped += 1;
  }
  return Match {remapped, region.query_id_idx, region.fwd_strand};
}

// In-order traversal of the implicit interval tree over intervals[low..high)
// collecting all intervals that contain pos. The first hit is written to `first`
// and any additional hits are appended to `extra`.
void Target::query_overlapping(std::size_t low, std::size_t high, std::int64_t pos,
                               Match & first, std::vector<Match> & extra, std::size_t & count) const {
  std::size_t mid = low + (high - low) / 2;
  // Prune the entire subtree if no interval in [low..high) extends past pos.
  if (pos >= max_stops[mid]) {
    return;
  }
  if (low < mid) {
    query_overlapping(low, mid, pos, first, extra, count);
  }
  const Interval & region = intervals[mid];
  // Because intervals are sorted by start, if region starts after pos then neither
  // region nor anything in the right subtree can contain pos.
  if (pos < region.start) {
    return;
  }
  if (pos < region.stop) {
    Match m = remap(region, pos);
    if (count == 0) {
      first = m;
    } else {
      extra.push_back(m);
    }
    ++count;
  }
  if (mid + 1 < high) {
    query_overlapping(mid + 1, high, pos, first, extra, count);
  }
}

std::size_t Target::query(std::int64_t pos, Match & first, std::vector<Match> & extra) const {
  // Chain intervals are stored in 0-based half-open coordinates; shift 1-based queries
  // down before lookup and reject out-of-range negative coordinates early.
  if (one_based) {
    if (pos < 1) {
      return 0;
    }
    pos -= 1;
  } else if (pos < 0) {
    return 0;
  }

  if (intervals.empty() || pos < intervals.front().start) {
    return 0;
  }

  // Fast path for non-overlapping intervals: only the last interval with start <= pos
  // can contain pos, so `extra` never needs to allocate.
  if (max_stops.empty()) {
    auto it = std::upper_bound(
      intervals.begin(), intervals.end(), pos,
      [](std::int64_t p, const Interval & iv) { return p < iv.start; });
    --it;
    if (pos < it->stop) {
      first = remap(*it, pos);
      return 1;
    }
    return 0;
  }

  if (!extra.empty()) {
    extra.clear();
  }
  std::size_t count = 0;
  query_overlapping(0, intervals.size(), pos, first, extra, count);
  return count;
}

} //namespace
