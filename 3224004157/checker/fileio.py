"""Read exactly the two requested inputs and write the requested answer."""

from pathlib import Path

from checker.errors import InvalidPathError, ResultWriteError, TextReadError
from checker.similarity import similarity


def _validate_paths(original: Path, candidate: Path, output: Path) -> None:
    """Reject relative paths and protect inputs, including aliases/hard links."""
    paths = (original, candidate, output)
    if any(not path.is_absolute() for path in paths):
        raise InvalidPathError("三个文件路径都必须是绝对路径。")
    try:
        resolved_original, resolved_candidate, resolved_output = (path.resolve() for path in paths)
        if resolved_output in (resolved_original, resolved_candidate):
            raise InvalidPathError("答案文件不能与任一输入文件相同，以免覆盖原文。")
        for path in (original, candidate):
            if not path.is_file():
                raise TextReadError(f"输入文件不存在或不是普通文件：{path}")
            if output.exists() and output.samefile(path):
                raise InvalidPathError("答案文件与输入文件指向同一个文件，不能覆盖。")
    except (OSError, RuntimeError, ValueError) as error:
        raise InvalidPathError(f"无法检查文件路径：{error}") from error


def _read_text(path: Path) -> str:
    """Read UTF-8 with optional BOM; never silently replace invalid bytes."""
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeError as error:
        raise TextReadError(f"文件不是有效的 UTF-8 文本，请先转换编码：{path}") from error
    except OSError as error:
        raise TextReadError(f"无法读取文件：{path}（{error}）") from error


def compare_files(original: Path, candidate: Path, output: Path) -> float:
    """Compare two files, save the two-decimal score, and return full precision."""
    _validate_paths(original, candidate, output)
    score = similarity(_read_text(original), _read_text(candidate))
    try:
        output.write_text(f"{score:.2f}\n", encoding="utf-8")
    except OSError as error:
        raise ResultWriteError(f"无法写入答案文件：{output}（{error}）") from error
    return score
