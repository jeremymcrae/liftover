// #include <string>

#include <stdexcept>

#include "chain.h"

namespace liftover {

inline void parse(std::string & line, std::int64_t & size, std::int64_t & target_gap, std::int64_t & query_gap) {
  /* parse an alignment data line
  
  line: an alignment line e.g. '5000\t10\t5' or '5000' Most lines have 3 items
    (size, reference delta, query delta), but the final line has only one (size).
  */
  bool has_delim = false;
  char delim = 0;
  if (line.find("\t") != std::string::npos) {
    delim = '\t';
    has_delim = true;
  } else if (line.find(" ") != std::string::npos) {
    delim = ' ';
    has_delim = true;
  }
  std::istringstream iss(line);
  std::string item;
  
  std::getline(iss, item, delim);
  size = std::stol(item);
  
  if (has_delim) {
    std::getline(iss, item, delim);
    target_gap = std::stol(item);
    std::getline(iss, item, delim);
    query_gap = std::stol(item);
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
  
  Mapped data = Mapped {query, query + size, query_id,
    query_strand == "+", query_size};
  intervals.push_back( Coords {target, target + size, data} );
  
  target += size + target_gap;
  query += size + query_gap;
}

// check the chain is valid, once complete
void Chain::validate() {
  if (target != target_end) {
    throw std::invalid_argument("target end does not match expectations");
  }

  if (query != query_end) {
    throw std::invalid_argument("query end does not match expectations");
  }
}

}  // namespace
