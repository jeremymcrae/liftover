#ifndef CHAIN_HEADERS_H
#define CHAIN_HEADERS_H

#include <cstdint>
#include <string>
#include <vector>
#include <cassert>

#include "utils.h"

namespace liftover {

struct ChainHeader {
    // hold header data for single chain
  std::string chain;
  std::int64_t score;
  std::string target_id;
  std::int64_t target_size;
  std::string target_strand;
  std::int64_t target_start;
  std::int64_t target_end;
  std::string query_id;
  std::int64_t query_size;
  std::string query_strand;
  std::int64_t query_start;
  std::int64_t query_end;
  std::string id;
};

ChainHeader process_header(std::string line);

} // namespace

#endif
