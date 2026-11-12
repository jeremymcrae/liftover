#ifndef LIFTOVER_UTILS_H
#define LIFTOVER_UTILS_H

#include <cstdint>
#include <limits>

namespace liftover {

/* parse a 64-bit integer from a character pointer with minimum value check.
   Skips leading whitespace, validates range and terminating delimiters,
   and advances ptr to the end of the parsed integer on success.
*/
inline bool parse_int64(const char *& ptr, std::int64_t & out, std::int64_t min_val = 0) {
  const char * p = ptr;
  while (*p == ' ' || *p == '\t') {
    ++p;
  }

  bool neg = false;
  if (*p == '-') {
    neg = true;
    ++p;
  } else if (*p == '+') {
    ++p;
  }

  if (*p < '0' || *p > '9') {
    return false;
  }

  const std::uint64_t max_pos = static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
  const std::uint64_t cutoff = max_pos / 10ULL;
  const std::uint64_t max_digit = neg ? 8ULL : 7ULL;
  std::uint64_t acc = 0;
  while (*p >= '0' && *p <= '9') {
    std::uint64_t digit = static_cast<std::uint64_t>(*p - '0');
    if (acc >= cutoff && (acc > cutoff || digit > max_digit)) {
      return false;
    }
    acc = acc * 10ULL + digit;
    ++p;
  }

  if (*p != '\0' && *p != ' ' && *p != '\t' && *p != '\r' && *p != '\n') {
    return false;
  }

  std::int64_t val = neg
    ? (acc == max_pos + 1ULL ? std::numeric_limits<std::int64_t>::min() : -static_cast<std::int64_t>(acc))
    : static_cast<std::int64_t>(acc);
  if (val < min_val) {
    return false;
  }

  ptr = p;
  out = val;
  return true;
}

} // namespace

#endif
