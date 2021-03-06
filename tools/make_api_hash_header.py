# Copyright (c) 2019 The Chromium Embedded Framework Authors. All rights
# reserved. Use of this source code is governed by a BSD-style license that
# can be found in the LICENSE file.

from __future__ import absolute_import
from cef_api_hash import cef_api_hash
from cef_parser import get_copyright
from file_util import *
import os
import sys


def make_api_hash_header(cpp_header_dir):
  # calculate api hashes
  api_hash_calculator = cef_api_hash(cpp_header_dir, verbose=False)
  api_hash = api_hash_calculator.calculate()

  result = get_copyright(full=True, translator=False) + \
"""//
// ---------------------------------------------------------------------------
//
// This file was generated by the make_api_hash_header.py tool.
//

#ifndef CEF_INCLUDE_API_HASH_H_
#define CEF_INCLUDE_API_HASH_H_

#include "include/internal/cef_export.h"

// The API hash is created by analyzing CEF header files for C API type
// definitions. The hash value will change when header files are modified in a
// way that may cause binary incompatibility with other builds. The universal
// hash value will change if any platform is affected whereas the platform hash
// values will change only if that particular platform is affected.
#define CEF_API_HASH_UNIVERSAL "$UNIVERSAL$"
#if defined(OS_WIN)
#define CEF_API_HASH_PLATFORM "$WINDOWS$"
#elif defined(OS_MACOSX)
#define CEF_API_HASH_PLATFORM "$MACOSX$"
#elif defined(OS_LINUX)
#define CEF_API_HASH_PLATFORM "$LINUX$"
#endif

#ifdef __cplusplus
extern "C" {
#endif

///
// Returns CEF API hashes for the libcef library. The returned string is owned
// by the library and should not be freed. The |entry| parameter describes which
// hash value will be returned:
// 0 - CEF_API_HASH_PLATFORM
// 1 - CEF_API_HASH_UNIVERSAL
// 2 - CEF_COMMIT_HASH (from cef_version.h)
///
CEF_EXPORT const char* cef_api_hash(int entry);

#ifdef __cplusplus
}
#endif
#endif  // CEF_INCLUDE_API_HASH_H_
"""

  # Substitute hash values for placeholders.
  for platform, value in api_hash.items():
    result = result.replace('$%s$' % platform.upper(), value)

  return result


def write_api_hash_header(output, cpp_header_dir):
  output = os.path.abspath(output)
  result = make_api_hash_header(cpp_header_dir)
  ret = write_file_if_changed(output, result)

  # Also write to |cpp_header_dir| if a different path from |output|, since we
  # need to commit the hash header for cef_version.py to correctly calculate the
  # version number based on git history.
  header_path = os.path.abspath(
      os.path.join(cpp_header_dir, os.path.basename(output)))
  if (output != header_path):
    write_file_if_changed(header_path, result)

  return ret


def main(argv):
  if len(argv) < 3:
    print(("Usage:\n  %s <output_filename> <cpp_header_dir>" % argv[0]))
    sys.exit(-1)
  write_api_hash_header(argv[1], argv[2])


if '__main__' == __name__:
  main(sys.argv)
