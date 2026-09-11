"""Usage: python3 main.py ORIGINAL_ABSOLUTE_PATH CANDIDATE_PATH ANSWER_PATH."""

import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

from checker.errors import CheckerError
from checker.fileio import compare_files

USAGE = "用法：python3 main.py <原文绝对路径> <待比较文本绝对路径> <答案文件绝对路径>"


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Return 0 for success/help, 2 for arguments, or 1 for file errors."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments in (["--help"], ["-h"]):
        print(USAGE)
        print("输入编码：UTF-8；结果：0～1 的相似度，保留两位小数。")
        return 0
    if len(arguments) != 3:
        print(USAGE, file=sys.stderr)
        return 2
    try:
        compare_files(*(Path(argument) for argument in arguments))
    except CheckerError as error:
        print(f"错误：{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
