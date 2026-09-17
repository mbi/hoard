# Script should be passed two paramters
# username and password
import sys

import crypt

if len(sys.argv) == 3:
    print(f"{sys.argv[1]}:{crypt.crypt(sys.argv[2], sys.argv[2])}")
