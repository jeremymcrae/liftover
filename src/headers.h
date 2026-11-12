#ifndef CHAIN_HEADERS_H
#define CHAIN_HEADERS_H

#include <cstdint>
#include <string>

#include "utils.h"

namespace liftover {

struct ChainHeader {
  // hold parsed header data for a single chain
  std::int64_t score;
  std::string target_id;
  std::int64_t target_size;
  std::int64_t target_start;
  std::int64_t target_end;
  std::string query_id;
  std::int64_t query_size;
  std::int64_t query_start;
  std::int64_t query_end;
  bool fwd_strand;
};

ChainHeader process_header(const std::string & line);

} // namespace

#endif
