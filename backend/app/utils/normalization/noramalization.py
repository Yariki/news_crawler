import unicodedata
import re

_INVISIBLE_CHARS = {
    "\u200b",  # ZERO WIDTH SPACE
    "\u200c",  # ZERO WIDTH NON‑JOINER
    "\u200d",  # ZERO WIDTH JOINER
    "\ufeff",  # ZERO WIDTH NO‑BREAK SPACE / BOM
}
_WHITESPACE_RE = re.compile(r"[ \t\f\v]+")


def remove_invisible_chars(text: str) -> str:
    """
    Remove invisible characters from the given text.

    Args:
        text (str): The input text from which to remove invisible characters.

    Returns:
        str: The text with invisible characters removed.
    """
    return "".join(c for c in text if c not in _INVISIBLE_CHARS)


def remove_control_chars(text: str) -> str:
    """
    Remove control characters from the given text.

    Args:
        text (str): The input text from which to remove control characters.

    Returns:
        str: The text with control characters removed.
    """
    return "".join(c for c in text  if not (ord(c) < 32 and c not in ("\n", "\t")))

def normalize_whitespace(text: str, max_whitespace: int) -> str:
    """
    Normalize whitespace in the given text by replacing consecutive whitespace characters with a single space.

    Args:
        text (str): The input text to normalize.
        max_whitespace (int): The maximum number of consecutive empty lines allowed.

    Returns:
        str: The text with normalized whitespace.
    """
    lines: list[str] = [ _WHITESPACE_RE.sub(" ", line).strip() for line in text.split("\n") ]
    cleaned: list[str] = []
    
    count = 0
    
    for line in lines:
        if line == "":
            count += 1
            if count <= max_whitespace:
                cleaned.append("")
        else:
            count = 0
            cleaned.append(line)

    return "\n".join(cleaned)
    

def normalize_newlines(text: str) -> str:
    """
    Normalize newlines in the given text by converting all newline variations to a single newline character.

    Args:
        text (str): The input text to normalize.

    Returns:
        str: The text with normalized newlines.
    """
    return text.replace("\r\n", "\n").replace("\r", "\n")   


_REP_PUNCT_RE = re.compile(r"([!?.])\1{3,}")  # 4+ repeats
def norm_repeated_punct(text: str, limit: int) -> str:
    """
    Normalize repeated punctuation in the given text by limiting consecutive occurrences.

    Args:
        text (str): The input text to normalize.
        limit (int): The maximum number of consecutive punctuation marks allowed.

    Returns:
        str: The text with normalized repeated punctuation.
    """
    def _truncate(m: re.Match[str]) -> str:
        return m.group(1) * min(len(m.group(0)), limit)
    return _REP_PUNCT_RE.sub(_truncate, text)


_DESH_RE = re.compile(r"[‑‑–—−]")
def normalize_dashes(text: str) -> str:
    """
    Normalize various dash characters in the given text to a standard hyphen.

    Args:
        text (str): The input text to normalize.

    Returns:
        str: The text with normalized dashes.
    """
    return _DESH_RE.sub("-", text)

_URL_RE = re.compile(
    r"https?://[^\s<>()]+", re.IGNORECASE
)
_MENTION_RE = re.compile(r"@([A-Za-z0-9_]{3,})")
_HASHTAG_RE = re.compile(r"#([^\s#@]+)")


def find_urls(text: str) -> list[str]:
    """
    Find all URLs in the given text.

    Args:
        text (str): The input text to search for URLs.

    Returns:
        list[str]: A list of URLs found in the text.
    """
    urls = _URL_RE.findall(text)
    return urls

def find_mentions(text: str, keep_mentions: bool = True) -> list[str]:
    """
    Find all mentions in the given text.

    Args:
        text (str): The input text to search for mentions.
        keep_mentions (bool): Whether to keep mentions in the result.

    Returns:
        list[str]: A list of mentions found in the text.
    """
    mentions = _MENTION_RE.findall(text) if keep_mentions else []
    return mentions

def find_hashtags(text: str, keep_hashtags: bool = True) -> list[str]:
    """
    Find all hashtags in the given text.

    Args:
        text (str): The input text to search for hashtags.
        keep_hashtags (bool): Whether to keep hashtags in the result.

    Returns:
        list[str]: A list of hashtags found in the text.
    """
    hashtags = _HASHTAG_RE.findall(text) if keep_hashtags else []
    return hashtags
