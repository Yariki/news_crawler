import re


ARTICLE_LINK_RE = re.compile(r"/\d{4}/\d{2}/\d{2}/.+-a\d+$")
ARTICLE_URL_PATTERN = re.compile(r"^/(\d{8})/.*\.html$")

PATTERNS = [
    ARTICLE_LINK_RE,
    ARTICLE_URL_PATTERN,
    re.compile(r"/\d{4}/\d{2}/\d{2}/.+-a\d+$"),
    re.compile(r"/(\d{8})/.*\.html$"),
    re.compile(r"news\/(\d{4,10}).*$"),
    re.compile(r"[news|article]\/(\d{4,10}).*$"),
    re.compile(r"article\/(\d{4,10}).*$"),
    re.compile(r"/news/\d{4}/\d{2}/\d{2}/.+\.html$"),
    re.compile(r"/\d{4}/\d{2}/\d{2}/.+\.html$"),
    re.compile(r"/news/\d{4}/\d{2}/\d{2}/.+-a\d+\.html$"),
    re.compile(r"/\d{4}/\d{2}/\d{2}/.+-a\d+\.html$"),
] 

LINK_RE = re.compile(r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)")
DATE_RE = re.compile(r"\b\d{2}\.\d{2}\.\d{4}\b")