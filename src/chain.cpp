#include <stdexcept>
#include <utility>

#include "chain.h"

namespace liftover {

inline void parse(const std::string & line, std::int64_t & size, std::int64_t & target_gap, std::int64_t & query_gap) {
  /* parse an alignment data line
  
  line: an alignment line e.g. '5000\t10\t5' or '5000' Most lines have 3 items
    (size, reference delta, query delta), but the final line has only one (size).
  */
  const char * ptr = line.c_str();
  // parse the alignment block size (must be >= 1)
  if (!parse_int64(ptr, size, 1)) {
    throw std::invalid_argument("invalid alignment line: " + line);
  }

  // skip any whitespace between items
  while (*ptr == ' ' || *ptr == '\t') {
    ptr++;
  }

  if (*ptr != '\0') {
    // if there are more items, parse the target gap
    if (!parse_int64(ptr, target_gap, 0)) {
      throw std::invalid_argument("invalid alignment line: " + line);
    }

    // move on to the final item (query gap)
    if (!parse_int64(ptr, query_gap, 0)) {
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
  auto it = query_indices.find(header.query_id);
  if (it == query_indices.end()) {
    query_id_idx = static_cast<std::uint32_t>(query_names.size());
    query_indices.emplace(header.query_id, query_id_idx);
    query_names.push_back(std::move(header.query_id));
  } else {
    query_id_idx = it->second;
  }
  query = header.query_start;
  fwd_strand = header.query_strand == "+";
  query_size = header.query_size;
  target_end = header.target_end;
  query_end = header.query_end;
}

void Chain::add_line(const std::string & line) {
  /* append an alignment interval directly to the target chromosome's vector
  */
  std::int64_t size = 0;
  std::int64_t target_gap = 0;
  std::int64_t query_gap = 0;
  parse(line, size, target_gap, query_gap);
  
  std::int64_t mapped_start = fwd_strand ? query : query_size - 1 - query;
  Mapped data = Mapped {mapped_start, query_id_idx, fwd_strand};
  dest->push_back(Interval {target, target + size, data});
  
  target += size + target_gap;
  query += size + query_gap;
}

// check the chain is valid, once complete
void Chain::validate() const {
  if (target != target_end) {
    throw std::invalid_argument("target end does not match expectations: " + std::to_string(target) + " != " + std::to_string(target_end));
  }

  if (query != query_end) {
    throw std::invalid_argument("query end does not match expectations: " + std::to_string(query) + " != " + std::to_string(query_end));
  }
}

}  // namespace
