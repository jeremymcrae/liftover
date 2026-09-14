#include <cstring>
#include <stdexcept>
#include <zlib.h>

#include "chain_file.h"

namespace liftover {

class GzReader {
  gzFile file;
  char buffer[65536];
  int buf_len = 0;
  int buf_pos = 0;
public:
  explicit GzReader(const char *path) {
    file = gzopen(path, "rb");
  }
  ~GzReader() {
    if (file) {
      gzclose(file);
    }
  }
  bool is_open() const { return file != nullptr; }

  bool getline(std::string &line) {
    line.clear();
    while (true) {
      if (buf_pos >= buf_len) {
        buf_len = gzread(file, buffer, sizeof(buffer));
        buf_pos = 0;
        if (buf_len <= 0) {
          return !line.empty();
        }
      }
      char *newline = static_cast<char *>(std::memchr(buffer + buf_pos, '\n', buf_len - buf_pos));
      if (newline != nullptr) {
        int len = newline - (buffer + buf_pos);
        line.append(buffer + buf_pos, len);
        buf_pos += len + 1;
        return true;
      } else {
        int len = buf_len - buf_pos;
        line.append(buffer + buf_pos, len);
        buf_pos = buf_len;
      }
    }
  }
};

std::map<std::string, Target> open_chainfile(std::string path, bool one_based) {
  /* open a gzipped liftover chain file, and parses contents
  
  This builds a map of Targets, indexed by chromosome, so we can quickly select
  the Target of interest when querying a given coordinate.
  */
  GzReader infile(path.c_str());
  if (!infile.is_open()) {
    throw std::invalid_argument("cannot open chain file at " + path);
  }

  std::string line;
  std::map<std::string, Tree::interval_vector> chrom_intervals;
  Chain chain;
  bool has_chain = false;

  while (infile.getline(line)) {
    // sanitize line endings
    if (!line.empty() && line.back() == '\r') {
      line.pop_back();
    }
    
    if (line.empty()) {
      // finish existing chain at blank lines
      if (has_chain) {
        chain.save_to(chrom_intervals[chain.target_id]);
        has_chain = false;
      }
    } else if (line[0] == '#') {
      // skip comment lines
      continue;
    } else if (line[0] == 'c' && (line.compare(0, 6, "chain ") == 0 || line.compare(0, 6, "chain\t") == 0)) {
      if (has_chain) {
        chain.save_to(chrom_intervals[chain.target_id]);
      }
      chain = Chain(line);
      has_chain = true;
    } else {
      if (!has_chain) {
        throw std::invalid_argument("alignment line found before chain header: " + line);
      }
      chain.add_line(line);
    }
  }

  if (has_chain) {
    // include the final chain, if the file doesn't end with a blank line
    chain.save_to(chrom_intervals[chain.target_id]);
  }
  
  // convert list of intervals into interval trees for each chromosome
  std::map<std::string, Target> targets;
  for (auto & x : chrom_intervals) {
    targets.emplace(x.first, Target(std::move(x.second), one_based));
  }
  return targets;
}

} //namespace
