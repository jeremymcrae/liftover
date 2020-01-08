
#include "headers.h"

namespace liftover {

ChainHeader process_header(std::string line) {
  /* process the header, and performs simple sanity checks
  */
  std::vector<std::string> hdr = split(line, ' ');
  ChainHeader header = ChainHeader {hdr[0], std::stoll(hdr[1]), hdr[2],
    std::stol(hdr[3]), hdr[4], std::stol(hdr[5]), std::stol(hdr[6]), hdr[7],
    std::stol(hdr[8]), hdr[9], std::stol(hdr[10]), std::stol(hdr[11]), hdr[12]};
  assert(header.chain == "chain");
  assert(header.target_strand == "+");
  assert(header.query_strand == "+" | header.query_strand == "-");
  return header;
}

} // namespace
