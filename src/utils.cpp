
#include "utils.h"

namespace liftover {

std::vector<std::string> split(const std::string &s, char delim) {
  /* split a string by delimiter into a vector of elements
  */
  std::vector<std::string> elems;
  std::istringstream iss(s);
  std::string item;
  while (std::getline(iss, item, delim)) {
    elems.push_back(item);
  }
  return elems;
}

} //namespace
