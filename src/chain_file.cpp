#include <cstring>
#include <stdexcept>
#include <sys/stat.h>
#include <unordered_map>
#include <vector>
#include <zlib.h>

#include "chain_file.h"

namespace liftover {

static bool is_directory(const char *path) {
  struct stat st;
  if (stat(path, &st) == 0) {
#if defined(S_ISDIR)
    return S_ISDIR(st.st_mode);
#elif defined(_S_IFDIR)
    return (st.st_mode & _S_IFDIR) != 0;
#else
    return false;
#endif
  }
  return false;
}

class GzReader {
  gzFile file;
  std::string path;
  char buffer[65536];
  int buf_len = 0;
  int buf_pos = 0;
public:
  explicit GzReader(const char *path) : file(gzopen(path, "rb")), path(path) {
    if (file) {
      gzbuffer(file, 65536);
    }
  }
  ~GzReader() {
    if (file) {
      gzclose_r(file);
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
          int errnum = 0;
          const char *msg = gzerror(file, &errnum);
          if (buf_len < 0 || (errnum != Z_OK && errnum != Z_STREAM_END)) {
            throw std::invalid_argument(msg && *msg ? msg : "error reading chain file: " + path);
          }
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

ChainFileResult open_chainfile(std::string path, bool one_based) {
  /* open a gzipped liftover chain file, and parses contents
  
  This builds a map of Targets, indexed by chromosome, so we can quickly select
  the Target of interest when querying a given coordinate.
  */
  if (is_directory(path.c_str())) {
    throw std::invalid_argument("cannot open directory as chain file: " + path);
  }

  GzReader infile(path.c_str());
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
