#include <algorithm>
#include <clocale>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <stdexcept>

#include "headers.h"

namespace liftover {

namespace {

// Non-owning slice into the header line, avoiding per-field string allocations.
struct Token {
  const char * ptr;
  std::size_t len;
};

inline bool is_ws(char c) {
  return c == ' ' || c == '\t' || c == '\r' || c == '\n';
}

// Advance cursor to the next whitespace-delimited token; returns false at end of line.
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

// Parse an entire token as an int64 >= min_val, throwing on invalid or partial tokens.
inline std::int64_t parse_header_int(const Token & tok, const std::string & line, std::int64_t min_val = 0) {
  const char * ptr = tok.ptr;
  std::int64_t val = 0;
  if (!parse_int64(ptr, val, min_val) || ptr != tok.ptr + tok.len) {
    throw std::invalid_argument("invalid header line: " + line);
  }
  return val;
}

// Validate the chain score token, which UCSC defines as a double (usually integer-formatted).
inline void validate_header_score(const Token & tok, const std::string & line) {
  const char * ptr = tok.ptr;
  std::int64_t int_val = 0;
  if (parse_int64(ptr, int_val, std::numeric_limits<std::int64_t>::min()) && ptr == tok.ptr + tok.len) {
    return;
  }

  // Fallback for decimal or scientific-notation scores (rejecting hex floats, inf, and nan).
  const char * p = tok.ptr;
  const char * end = p + tok.len;
  if (p < end && (*p == '+' || *p == '-')) {
    ++p;
  }
  std::size_t digits = 0;
  while (p < end && *p >= '0' && *p <= '9') {
    ++p;
    ++digits;
  }
  if (p < end && *p == '.') {
    ++p;
    while (p < end && *p >= '0' && *p <= '9') {
      ++p;
      ++digits;
    }
  }
  if (digits == 0) {
    throw std::invalid_argument("invalid header line: " + line);
  }
  if (p < end && (*p == 'e' || *p == 'E')) {
    ++p;
    if (p < end && (*p == '+' || *p == '-')) {
      ++p;
    }
    if (p == end || *p < '0' || *p > '9') {
      throw std::invalid_argument("invalid header line: " + line);
    }
    while (p < end && *p >= '0' && *p <= '9') {
      ++p;
    }
  }
  if (p != end) {
    throw std::invalid_argument("invalid header line: " + line);
  }

  std::string buf(tok.ptr, tok.len);
  char radix = std::localeconv()->decimal_point[0];
  if (radix != '.') {
    std::replace(buf.begin(), buf.end(), '.', radix);
  }
  char * stop = nullptr;
  double val = std::strtod(buf.c_str(), &stop);
  if (!std::isfinite(val) || stop != buf.c_str() + buf.size()) {
    throw std::invalid_argument("invalid header line: " + line);
  }
}

} // namespace

ChainHeader process_header(const std::string & line) {
  // UCSC chain header format (13 whitespace-separated fields):
  //   0:chain  1:score  2:tName  3:tSize  4:tStrand  5:tStart  6:tEnd
  //   7:qName  8:qSize  9:qStrand 10:qStart 11:qEnd 12:id
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

  // Validate score and target_size even though Chain does not need to store them.
  validate_header_score(hdr[1], line);
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
  // Reverse-strand query coordinates are measured from the end of query_size, so
  // query_end > query_size would map positions to negative forward coordinates.
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
