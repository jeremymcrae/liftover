
#include "utils.h"

namespace liftover {

std::vector<std::string> split(const std::string &s) {
  /* split a string by whitespace (spaces, tabs, newlines) into elements,
     skipping runs of delimiters and leading/trailing whitespace.
  */
  std::vector<std::string> elems;
  elems.reserve(13);
  const char *ptr = s.c_str();
  while (*ptr != '\0') {
    while (*ptr == ' ' || *ptr == '\t' || *ptr == '\r' || *ptr == '\n') {
      ptr++;
    }
    if (*ptr == '\0') {
      break;
    }
    const char *start = ptr;
    while (*ptr != '\0' && *ptr != ' ' && *ptr != '\t' && *ptr != '\r' && *ptr != '\n') {
      ptr++;
    }
    elems.emplace_back(start, ptr - start);
  }
  return elems;
}

} //namespace
