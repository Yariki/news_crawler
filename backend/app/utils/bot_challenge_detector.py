CHALLENGE_MARKERS = (
    "please enable js",
    "please enable javascript",
    "disable any ad blocker",
    "attention required",
    "cf-browser-verification",
    "cloudflare",
    "datadome",
    "just a moment...",
)


def looks_like_bot_challenge(self, html: str) -> bool:
    text = html.lower()
    return any(marker in text for marker in self.CHALLENGE_MARKERS)
