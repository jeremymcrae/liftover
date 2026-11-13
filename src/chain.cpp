#include <stdexcept>
#include <utility>

#include "chain.h"

namespace liftover {

// Parse an alignment block line: either "size dt dq" (ungapped block followed by
// target and query gaps) or "size" on the final block of a chain.
inline void parse(const std::string & line, std::int64_t & size, std::int64_t & target_gap, std::int64_t & query_gap) {
  const char * ptr = line.c_str();
  if (!parse_int64(ptr, size, 1)) {
    throw std::invalid_argument("invalid alignment line: " + line);
  }

  while (*ptr == ' ' || *ptr == '\t') {
    ptr++;
  }

  if (*ptr != '\0') {
    if (!parse_int64(ptr, target_gap, 0) || !parse_int64(ptr, query_gap, 0)) {
      throw std::invalid_argument("invalid alignment line: " + line);
    }
  } else {
    target_gap = 0;
    query_gap = 0;
  }
}

Chain::Chain(const std::string & header_line,
             std::unordered_map<std::string, std::vector<Interval>> & chrom_intervals,
             std::vector<std::string> & query_names,
             std::unordered_map<std::string, std::uint32_t> & query_indices) {
  ChainHeader header = process_header(header_line);
  dest = &chrom_intervals[std::move(header.target_id)];
  target = header.target_start;

  // Intern query contig names so each Interval stores a 32-bit index rather than a string.
  auto it = query_indices.find(header.query_id);
  if (it == query_indices.end()) {
    query_id_idx = static_cast<std::uint32_t>(query_names.size());
    query_indices.emplace(header.query_id, query_id_idx);
    query_names.push_back(std::move(header.query_id));
  } else {
    query_id_idx = it->second;
  }

  query = header.query_start;
  fwd_strand = header.fwd_strand;
  query_size = header.query_size;
  target_end = header.target_end;
  query_end = header.query_end;
}

void Chain::add_line(const std::string & line) {
  std::int64_t size = 0;
  std::int64_t target_gap = 0;
  std::int64_t query_gap = 0;
  parse(line, size, target_gap, query_gap);

  // Check remaining span via subtraction so huge values cannot overflow int64_t.
  if (size > target_end - target || target_gap > target_end - target - size) {
    throw std::invalid_argument("target alignment exceeds header target_end: " + line);
  }
  if (size > query_end - query || query_gap > query_end - query - size) {
    throw std::invalid_argument("query alignment exceeds header query_end: " + line);
  }

  // On '-' strand, UCSC chain query coordinates count from the reverse-complement end,
  // so target+offset maps to (query_size - 1 - query) - offset on the forward strand.
  std::int64_t mapped_start = fwd_strand ? query : query_size - 1 - query;
  dest->push_back(Interval {target, target + size, mapped_start, query_id_idx, fwd_strand});

  target += size + target_gap;
  query += size + query_gap;
}

// Verify that the sum of alignment blocks and gaps matches the header's end coordinates.
void Chain::validate() const {
  if (target != target_end) {
    throw std::invalid_argument("target end does not match expectations: " + std::to_string(target) + " != " + std::to_string(target_end));
  }

  if (query != query_end) {
    throw std::invalid_argument("query end does not match expectations: " + std::to_string(query) + " != " + std::to_string(query_end));
  }
}

}  // namespace
