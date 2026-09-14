
#include <climits>
#include <stdexcept>

#include "headers.h"

namespace liftover {

static std::int64_t parse_header_int(const std::string & s, const std::string & line, std::int64_t min_val = 0) {
  const char * ptr = s.c_str();
  std::int64_t val = 0;
  if (!parse_int64(ptr, val, min_val)) {
    throw std::invalid_argument("invalid header line: " + line);
  }
  return val;
}

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

  std::int64_t score = parse_header_int(hdr[1], line, LLONG_MIN);
  std::int64_t target_size = parse_header_int(hdr[3], line);
  std::int64_t target_start = parse_header_int(hdr[5], line);
  std::int64_t target_end = parse_header_int(hdr[6], line);
  std::int64_t query_size = parse_header_int(hdr[8], line);
  std::int64_t query_start = parse_header_int(hdr[10], line);
  std::int64_t query_end = parse_header_int(hdr[11], line);

  ChainHeader header = ChainHeader {hdr[0], score, hdr[2],
    target_size, hdr[4], target_start, target_end, hdr[7],
    query_size, hdr[9], query_start, query_end, hdr[12]};
  
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
