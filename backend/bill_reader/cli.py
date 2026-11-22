"""python -m backend.bill_reader.cli <bill.pdf|bill.jpg|bill.png>"""

from __future__ import annotations

import json
import mimetypes
import sys
from pathlib import Path

from .reader import read_bill


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    path = Path(args[0])
    ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    result = read_bill(path.read_bytes(), ctype)
    print(json.dumps(result.to_dict(), indent=2))
    print(f"\n[{result.seconds:.1f}s, {result.model}, tokens in {result.input_tokens} / out {result.output_tokens}]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
