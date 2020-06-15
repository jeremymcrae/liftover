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
  
  std::istringstream iss(line);
  std::string item;
  
  std::getline(iss, item, '\t');
  size = std::stol(item);
  
  if (line.size() > 0) {
    std::getline(iss, item, '\t');
    target_gap = std::stol(item);
    std::getline(iss, item, '\t');
    query_gap = std::stol(item);
  } else {
    target_gap = 0;
    query_gap = 0;
  }
}

Chain::Chain(std::vector<std::string> & lines) {
  /* build a set of Intervals for mapping betwen coordinates.
  
  This uses the lines for a single chain. Chains for a single chromosome are
  collected together at a later stage.
  */
  ChainHeader header = process_header(lines[0]);
  lines.erase(lines.begin());
  intervals.resize(lines.size());
  
  target_id = header.target_id;
  long target = header.target_start;
  long query = header.query_start;
  
  long size;
  long target_gap;
  long query_gap;
  
  int i = 0;
  for (auto & line: lines) {
    parse(line, size, target_gap, query_gap);
    
    Mapped data = Mapped {query, query + size, header.query_id,
      header.query_strand == "+", header.query_size};
    intervals[i] = Coords {target, target + size, data};
    i += 1;
    
    target += size + target_gap;
    query += size + query_gap;
  }
  assert(target == header.target_end);
  assert(query == header.query_end);
}

}  // namespace
