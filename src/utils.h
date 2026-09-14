#ifndef LIFTOVER_UTILS_H
#define LIFTOVER_UTILS_H

#include <vector>
#include <string>
#include <sstream>
#include <cstdint>
#include <cstdlib>
#include <cerrno>

namespace liftover {

/* parse a 64-bit integer from a character pointer with minimum value check.
   Skips leading whitespace, validates range and terminating delimiters,
   and advances ptr to the end of the parsed integer on success.
*/
inline bool parse_int64(const char *& ptr, std::int64_t & out, std::int64_t min_val = 0) {
  char * end = nullptr;
  errno = 0;
  // parse the integer (strtoll automatically skips leading whitespace)
  long long val = std::strtoll(ptr, &end, 10);
  // check for overflow, missing digits, or value below minimum
  if (errno == ERANGE || end == ptr || val < min_val) {
    return false;
  }
  // verify number is terminated by end-of-string or whitespace delimiter
  if (*end != '\0' && *end != ' ' && *end != '\t') {
    return false;
  }
  // advance pointer past parsed digits and assign output
  ptr = end;
  out = val;
  return true;
}

std::vector<std::string> split(const std::string &s, char delim);

} // namespace

#endif
