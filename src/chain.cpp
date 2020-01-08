// #include <string>

#include "chain.h"

namespace liftover {

std::vector<long> parse(std::string line) {
  /* parse an alignment data line
  
  line: an alignment line e.g. '5000\t10\t5' or '5000' Most lines have 3 items
    (size, reference delta, query delta), but the final line has only one (size).
      
  returns vector of (size, delta_reference, delta_query). Last lines deltas = 0.
  */
  std::vector<std::string> result = split(line, '\t');
  std::vector<long> coords;
  if (result.size() == 3) {
    coords = {std::stol(result[0]), std::stol(result[1]), std::stol(result[2])};
  } else {
    coords = {std::stol(result[0]), 0, 0};
  }
  return coords;
}

Chain::Chain(std::vector<std::string> lines) {
  /* build a set of Intervals for mapping betwen coordinates.
  
  This uses the lines for a single chain. Chains for a single chromosome are
  collected together at a later stage.
  */
  ChainHeader header = process_header(lines[0]);
  lines.erase(lines.begin());
  target_id = header.target_id;
  long target = header.target_start;
  long query = header.query_start;
  for (auto line: lines) {
    std::vector<long> result = parse(line);
    long size = result[0];
    long target_gap = result[1];
    long query_gap = result[2];
    
    Mapped data = Mapped {query, query + size, header.query_id,
      header.query_strand == "+", header.query_size};
    intervals.push_back(Coords {target, target + size, data});
    
    target += size + target_gap;
    query += size + query_gap;
  }
  assert(target == header.target_end);
  assert(query == header.query_end);
}

}  // namespace
