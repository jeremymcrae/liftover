#ifndef LIFTOVER_CHAIN_H
#define LIFTOVER_CHAIN_H

#include <cstdint>
#include <vector>
#include <string>
#include <unordered_map>

#include "headers.h"

namespace liftover {

struct Interval {
  // half-open target interval [start, stop) and its mapped query origin.
  // For reverse-strand chains, mapped_start is precomputed as
  // (query_size - 1 - query_start) so queries only add or subtract the offset.
  std::int64_t start;
  std::int64_t stop;
  std::int64_t mapped_start;
  std::uint32_t query_id_idx;
  bool fwd_strand;
};

class Chain {
  // tracks state while parsing alignment lines for a single chain
  std::vector<Interval> * dest = nullptr;
  std::int64_t target = 0;
  std::int64_t query = 0;
  std::int64_t query_size = 0;
  std::int64_t target_end = 0;
  std::int64_t query_end = 0;
  std::uint32_t query_id_idx = 0;
  bool fwd_strand = true;
public:
  Chain() = default;
  Chain(const std::string & header_line,
        std::unordered_map<std::string, std::vector<Interval>> & chrom_intervals,
        std::vector<std::string> & query_names,
        std::unordered_map<std::string, std::uint32_t> & query_indices);
  void add_line(const std::string & line);
  void validate() const;
};

} //namespace

#endif
