
#include "headers.h"

namespace liftover {

ChainHeader process_header(std::string & line) {
  /* process the header, and performs simple sanity checks
  */
  std::vector<std::string> hdr;
  if (line.find("\t") != std::string::npos) {
    hdr = split(line, '\t');
  } else if (line.find(" ") != std::string::npos) {
    hdr = split(line, ' ');
  }

  if (hdr.size() != 13) {
    throw std::invalid_argument("invalid header line: " + line);
  }

  ChainHeader header = ChainHeader {hdr[0], std::stoll(hdr[1]), hdr[2],
    std::stol(hdr[3]), hdr[4], std::stol(hdr[5]), std::stol(hdr[6]), hdr[7],
    std::stol(hdr[8]), hdr[9], std::stol(hdr[10]), std::stol(hdr[11]), hdr[12]};
  
  if (header.chain != "chain") {
    throw std::invalid_argument("header line does not start with 'chain': " + line);
  }
  if (header.target_strand != "+") {
    throw std::invalid_argument("target strand is not '+': " + line);
  }
  if (header.query_strand != "+" && header.query_strand != "-") {
    throw std::invalid_argument("query strand is not '+' or '-': " + line);
  }
  
  return header;
}

} // namespace
