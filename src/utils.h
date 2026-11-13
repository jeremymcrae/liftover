#ifndef LIFTOVER_UTILS_H
#define LIFTOVER_UTILS_H

#include <cstdint>
#include <limits>

namespace liftover {

// Parse a base-10 signed 64-bit integer from ptr, requiring val >= min_val.
// Skips leading spaces/tabs, checks for overflow and trailing non-whitespace,
// and advances ptr past the digits on success.
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

  // Accumulate magnitude in uint64_t so INT64_MIN (2^63) can be represented
  // without signed overflow; max_digit is 8 for negative (-9223372036854775808)
  // and 7 for positive (9223372036854775807).
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

  // Reject trailing characters attached to the number (e.g. "123abc").
  if (*p != '\0' && *p != ' ' && *p != '\t' && *p != '\r' && *p != '\n') {
    return false;
  }

  // Convert magnitude to signed int64_t, handling INT64_MIN without negating 2^63.
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
