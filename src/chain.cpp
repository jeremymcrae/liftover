// #include <string>

#include "chain.h"

namespace liftover {

// inline void parse(std::string & line, long * coords) {
inline void parse(std::string & line, long & size, long & target_gap, long & query_gap) {
  /* parse an alignment data line
  
  line: an alignment line e.g. '5000\t10\t5' or '5000' Most lines have 3 items
    (size, reference delta, query delta), but the final line has only one (size).
  */
  // std::memset(coords, 0, 3);
  
  char delim = '\t';
  if (line.find(" ") != std::string::npos) {
    delim = ' ';
  }
  std::istringstream iss(line);
  std::string item;
  
  std::getline(iss, item, delim);
  size = std::stol(item);
  
  if (line.size() > 0) {
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
  
  assert(target == target_end);
  assert(query == query_end);
}

}  // namespace
