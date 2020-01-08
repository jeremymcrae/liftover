#ifndef LIFTOVER_CHAINFILE_H
#define LIFTOVER_CHAINFILE_H

#include <vector>
#include <string>
#include <map>

#include "gzstream/gzstream.h"

#include "chain.h"
#include "target.h"

namespace liftover {

std::map<std::string, Target> open_chainfile(std::string path);

}

#endif
