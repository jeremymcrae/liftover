#ifndef CHAIN_HEADERS_H
#define CHAIN_HEADERS_H

#include <string>
#include <vector>
#include <cassert>

#include "utils.h"

namespace liftover {

struct ChainHeader {
    // hold header data for single chain
  std::string chain;
  long long score;
  std::string target_id;
  long target_size;
  std::string target_strand;
  long target_start;
  long target_end;
  std::string query_id;
  long query_size;
  std::string query_strand;
  long query_start;
  long query_end;
  std::string id;
};

ChainHeader process_header(std::string line);

} // namespace

#endif
