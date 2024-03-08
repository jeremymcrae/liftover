/* example code for loading liftover chains and searching a given position
*/

#include <stdexcept>
#include <iostream>
#include <cstdint>

#include "chain_file.h"

int main() {
  // load liftover chain file
  std::string path = "/home/jmcrae/.liftover/hg38ToHg19.over.chain.gz";
  std::map<std::string, liftover::Target> targets = liftover::open_chainfile(path);
  
  // search for a given coordinate
  std::string chrom = "chr1";
  std::int64_t start = 10000000;
  std::int64_t size = 1000000;
  for (std::uint64_t pos=start; pos < (start + size); pos++) {
    if (!targets.count(chrom)) {
      throw std::invalid_argument("chromosome isn't in chain file: " + chrom);
    }

    for (auto x : targets[chrom][pos]) {
      std::cout << x.contig << " pos: " << x.pos << ", on fwd:"
                << x.fwd_strand << std::endl;
    }
  }
}

// set LD_FLAGS -fsanitize=undefined,address
// g++ -Weverything -Wno-padded -Wno-c++98-compat -stdlib=libc++ -std=c++11  \
//      -fsanitize=undefined,address \
//      -lz \
//      main.cpp chain_file.cpp chain.cpp headers.cpp target.cpp utils.cpp gzstream/gzstream.C
