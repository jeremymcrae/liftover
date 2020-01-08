/* example code for loading liftover chains and searching a given position
*/

#include "chain_file.h"

int main() {
  // load liftover chain file
  std::string path = "/home/jmcrae/.liftover/hg38ToHg19.over.chain.gz";
  std::map<std::string, liftover::Target> targets = liftover::open_chainfile(path);
  
  // search for a given coordinate
  std::string chrom = "chr1";
  long pos = 10000000;
  for (auto x : targets[chrom][pos]) {
    std::cout << x.contig << " pos: " << x.pos << ", on fwd:"
              << x.fwd_strand << std::endl;
  }
}
