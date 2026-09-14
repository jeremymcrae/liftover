
#include <stdexcept>

#include "chain.h"

namespace liftover {

inline void parse(std::string & line, std::int64_t & size, std::int64_t & target_gap, std::int64_t & query_gap) {
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

Chain::Chain(std::string & header_line) {
  ChainHeader header = process_header(header_line);
  target_id = header.target_id;
  target = header.target_start;
  query_id = header.query_id;
  query = header.query_start;
  query_strand = header.query_strand;
  query_size = header.query_size;
  target_end = header.target_end;
  query_end = header.query_end;
}

void Chain::add_line(std::string & line) {
  /* build a set of Intervals for mapping betwen coordinates.
  
  This uses the lines for a single chain. Chains for a single chromosome are
  collected together at a later stage.
  */
  parse(line, size, target_gap, query_gap);
  
  Mapped data = Mapped {query, query_id,
    query_strand == "+", query_size};
  intervals.push_back( Tree::interval(target, target + size, std::move(data)) );
  
  target += size + target_gap;
  query += size + query_gap;
}

// check the chain is valid, once complete
void Chain::validate() {
  if (target != target_end) {
    throw std::invalid_argument("target end does not match expectations: " + std::to_string(target) + " != " + std::to_string(target_end));
  }

  if (query != query_end) {
    throw std::invalid_argument("query end does not match expectations: " + std::to_string(query) + " != " + std::to_string(query_end));
  }
}

// validate and move intervals to destination chromosome vector
void Chain::save_to(Tree::interval_vector & dest) {
  validate();
  if (dest.empty()) {
    dest = std::move(intervals);
  } else {
    dest.insert(dest.end(),
                std::make_move_iterator(intervals.begin()),
                std::make_move_iterator(intervals.end()));
    intervals.clear();
  }
}

}  // namespace
