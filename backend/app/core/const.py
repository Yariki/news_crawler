import re


ARTICLE_LINK_RE = re.compile(r"/\d{4}/\d{2}/\d{2}/.+-a\d+$")
DATE_RE = re.compile(r"\b\d{2}\.\d{2}\.\d{4}\b")