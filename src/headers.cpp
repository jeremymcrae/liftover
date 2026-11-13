#include <cstring>
#include <limits>
#include <stdexcept>

#include "headers.h"

namespace liftover {

namespace {

struct Token {
  const char * ptr;
  std::size_t len;
};

inline bool is_ws(char c) {
  return c == ' ' || c == '\t' || c == '\r' || c == '\n';
}

inline bool next_token(const char *& cursor, Token & tok) {
  while (is_ws(*cursor)) {
    ++cursor;
  }
  if (*cursor == '\0') {
    return false;
  }
  tok.ptr = cursor;
  while (*cursor != '\0' && !is_ws(*cursor)) {
    ++cursor;
  }
  tok.len = static_cast<std::size_t>(cursor - tok.ptr);
  return true;
}

inline std::int64_t parse_header_int(const Token & tok, const std::string & line, std::int64_t min_val = 0) {
  const char * ptr = tok.ptr;
  std::int64_t val = 0;
  if (!parse_int64(ptr, val, min_val) || ptr != tok.ptr + tok.len) {
    throw std::invalid_argument("invalid header line: " + line);
  }
  return val;
}

} // namespace

ChainHeader process_header(const std::string & line) {
  /* parse a 13-field chain header in-place without intermediate string allocations
  */
  Token hdr[13];
  const char * cursor = line.c_str();
  for (std::size_t i = 0; i < 13; ++i) {
    if (!next_token(cursor, hdr[i])) {
      throw std::invalid_argument("invalid header line: " + line);
    }
  }
  while (is_ws(*cursor)) {
    ++cursor;
  }
  if (*cursor != '\0') {
    throw std::invalid_argument("invalid header line: " + line);
  }

  (void)parse_header_int(hdr[1], line, std::numeric_limits<std::int64_t>::min());
  (void)parse_header_int(hdr[3], line);
  std::int64_t target_start = parse_header_int(hdr[5], line);
  std::int64_t target_end = parse_header_int(hdr[6], line);
  std::int64_t query_size = parse_header_int(hdr[8], line);
  std::int64_t query_start = parse_header_int(hdr[10], line);
  std::int64_t query_end = parse_header_int(hdr[11], line);

  if (hdr[0].len != 5 || std::memcmp(hdr[0].ptr, "chain", 5) != 0) {
    throw std::invalid_argument("header line does not start with 'chain': " + line);
  }
  if (hdr[4].len != 1 || hdr[4].ptr[0] != '+') {
    throw std::invalid_argument("target strand is not '+': " + line);
  }
  if (hdr[9].len != 1 || (hdr[9].ptr[0] != '+' && hdr[9].ptr[0] != '-')) {
    throw std::invalid_argument("query strand is not '+' or '-': " + line);
  }
  bool fwd_strand = hdr[9].ptr[0] == '+';
  if (target_start > target_end || query_start > query_end) {
    throw std::invalid_argument("invalid header coordinates: " + line);
  }
  if (!fwd_strand && query_end > query_size) {
    throw std::invalid_argument("invalid header coordinates: " + line);
  }

  return ChainHeader {
    std::string(hdr[2].ptr, hdr[2].len),
    target_start,
    target_end,
    std::string(hdr[7].ptr, hdr[7].len),
    query_size,
    query_start,
    query_end,
    fwd_strand,
  };
}

} // namespace
