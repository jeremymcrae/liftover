#include <cstring>
#include <stdexcept>
#include <unordered_map>
#include <vector>
#include <zlib.h>

#include "chain_file.h"

namespace liftover {

class GzReader {
  gzFile file;
  std::string path;
  char buffer[65536];
  int buf_len = 0;
  int buf_pos = 0;
public:
  GzReader(int & fd, const std::string & path) : file(gzdopen(fd, "rb")), path(path) {
    if (file) {
      fd = -1;
      gzbuffer(file, 65536);
    }
  }
  GzReader(const GzReader &) = delete;
  GzReader & operator=(const GzReader &) = delete;
  ~GzReader() {
    if (file) {
      gzclose_r(file);
    }
  }
  bool is_open() const { return file != nullptr; }

  bool getline(std::string & line) {
    line.clear();
    while (true) {
      if (buf_pos >= buf_len) {
        buf_len = gzread(file, buffer, sizeof(buffer));
        buf_pos = 0;
        if (buf_len <= 0) {
          int errnum = 0;
          const char * msg = gzerror(file, &errnum);
          if (buf_len < 0 || (errnum != Z_OK && errnum != Z_STREAM_END)) {
            throw std::invalid_argument(msg && *msg ? msg : "error reading chain file: " + path);
          }
          return !line.empty();
        }
      }
      std::size_t rem = static_cast<std::size_t>(buf_len - buf_pos);
      char * newline = static_cast<char *>(std::memchr(buffer + buf_pos, '\n', rem));
      if (newline != nullptr) {
        std::size_t len = static_cast<std::size_t>(newline - (buffer + buf_pos));
        line.append(buffer + buf_pos, len);
        buf_pos += static_cast<int>(len) + 1;
        return true;
      } else {
        line.append(buffer + buf_pos, rem);
        buf_pos = buf_len;
      }
    }
  }
};

ChainFileResult open_chainfile(int & fd, const std::string & path, bool one_based) {
  /* open a liftover chain descriptor and index intervals per chromosome
  */
  GzReader infile(fd, path);
  if (!infile.is_open()) {
    throw std::invalid_argument("cannot open chain file at " + path);
  }

  std::string line;
  std::unordered_map<std::string, std::vector<Interval>> chrom_intervals;
  std::vector<std::string> query_names;
  std::unordered_map<std::string, std::uint32_t> query_indices;
  Chain chain;
  bool has_chain = false;

  while (infile.getline(line)) {
    while (!line.empty() && line.back() == '\r') {
      line.pop_back();
    }
    std::size_t first = 0;
    while (first < line.size() && (line[first] == ' ' || line[first] == '\t')) {
      ++first;
    }

    if (first == line.size()) {
      // finish existing chain at blank or whitespace-only lines
      if (has_chain) {
        chain.validate();
        has_chain = false;
      }
    } else if (line[first] == '#') {
      // skip comment lines
      continue;
    } else if (line[first] == 'c' &&
               line.size() - first >= 6 &&
               std::memcmp(line.data() + first, "chain", 5) == 0 &&
               (line[first + 5] == ' ' || line[first + 5] == '\t')) {
      if (has_chain) {
        chain.validate();
      }
      chain = Chain(line, chrom_intervals, query_names, query_indices);
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
    chain.validate();
  }

  // index intervals for each chromosome
  std::map<std::string, Target> targets;
  for (auto & x : chrom_intervals) {
    targets.emplace(x.first, Target(std::move(x.second), one_based));
  }
  return ChainFileResult {std::move(targets), std::move(query_names)};
}

} //namespace
