
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from collections import Counter
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

USERNAME = "AdriaCortez"

API_BASE = "https://api.github.com"

ASSETS_DIR = Path("assets")
ASSETS_DIR.mkdir(exist_ok=True)

TOKEN = os.getenv("GITHUB_TOKEN")

COLORS = {
    "background": "#090909",
    "surface": "#110B0E",
    "wine": "#3D0718",
    "border": "#641528",
    "red": "#E63946",
    "pink": "#FF6B81",
    "light_pink": "#FFB3C1",
    "text": "#F5F0F2",
    "muted": "#A99AA2",
    "track": "#302128",
}

PALETTE = [
    "#E63946",
    "#FF6B81",
    "#B91C3C",
    "#FFB3C1",
    "#8D2440",
    "#D94A70",
    "#A52A4A",
    "#F08090",
]

LANGUAGE_COLORS = {
    "TypeScript": "#3178C6",
    "JavaScript": "#F1E05A",
    "Python": "#3572A5",
    "Java": "#B07219",
    "HTML": "#E34C26",
    "CSS": "#563D7C",
    "Shell": "#89E051",
    "C": "#555555",
    "C++": "#F34B7D",
    "C#": "#178600",
    "Go": "#00ADD8",
    "Rust": "#DEA584",
    "PHP": "#4F5D95",
    "Ruby": "#701516",
    "Dart": "#00B4AB",
    "Kotlin": "#A97BFF",
    "Swift": "#F05138",
    "Vue": "#41B883",
}

def github_get(endpoint, params=None):

    query = ""

    if params:
        query = "?" + urllib.parse.urlencode(params)

    url = API_BASE + endpoint + query

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "BLOOD-GARDEN-GitHub-Stats",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    request = urllib.request.Request(
        url,
        headers=headers
    )

    for attempt in range(4):

        try:
            with urllib.request.urlopen(
                request,
                timeout=30
            ) as response:

                return json.loads(
                    response.read().decode("utf-8")
                )

        except urllib.error.HTTPError as error:

            if error.code in (403, 429, 500, 502, 503, 504):

                retry_after = error.headers.get("Retry-After")

                if retry_after:
                    wait = int(retry_after)
                else:
                    wait = min(2 ** attempt, 30)

                if attempt < 3:
                    print(
                        f"API limit/error {error.code}. "
                        f"Retrying in {wait}s..."
                    )
                    time.sleep(wait)
                    continue

            details = error.read().decode(
                "utf-8",
                errors="replace"
            )

            raise RuntimeError(
                f"GitHub API error {error.code}: {details}"
            ) from error

        except urllib.error.URLError as error:

            if attempt < 3:
                time.sleep(2 ** attempt)
                continue

            raise RuntimeError(
                f"Connection error: {error}"
            ) from error


def get_public_repositories():

    repositories = []
    page = 1

    while True:

        data = github_get(
            f"/users/{USERNAME}/repos",
            {
                "type": "owner",
                "per_page": 100,
                "page": page,
                "sort": "updated",
            }
        )

        if not data:
            break

        repositories.extend(data)

        if len(data) < 100:
            break

        page += 1

    return repositories


def get_language_distribution(repositories):

    language_totals = Counter()
    dominant_languages = {}

    for index, repo in enumerate(repositories, start=1):

        name = repo["name"]

        print(
            f"[LANGUAGES] {index}/{len(repositories)} "
            f"Analyzing {name}"
        )

        endpoint = (
            f"/repos/{USERNAME}/{name}/languages"
        )

        languages = github_get(endpoint)

        for language, byte_count in languages.items():

            language_totals[language] += byte_count

        if languages:

            dominant_languages[name] = max(
                languages,
                key=languages.get
            )

        else:

            dominant_languages[name] = "Other"

    return language_totals, dominant_languages

def get_commit_distribution(
    repositories,
    dominant_languages
):

    commits_by_language = Counter()

    cutoff = (
        datetime.now(timezone.utc)
        - timedelta(days=365)
    )

    since = cutoff.isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")

    seen_commits = set()

    for index, repo in enumerate(repositories, start=1):

        name = repo["name"]

        print(
            f"[COMMITS] {index}/{len(repositories)} "
            f"Analyzing {name}"
        )

        page = 1

        language = dominant_languages.get(
            name,
            "Other"
        )

        while True:

            data = github_get(
                f"/repos/{USERNAME}/{name}/commits",
                {
                    "author": USERNAME,
                    "since": since,
                    "per_page": 100,
                    "page": page,
                }
            )

            if not data:
                break

            for commit in data:

                sha = commit.get("sha")

                if not sha:
                    continue

                if sha in seen_commits:
                    continue

                seen_commits.add(sha)

                commits_by_language[language] += 1

            if len(data) < 100:
                break

            page += 1

    return commits_by_language


def pixel_lily(x, y, scale=3):

    pixels = [
        (2, 0, COLORS["pink"]),
        (3, 0, COLORS["red"]),
        (1, 1, COLORS["red"]),
        (2, 1, COLORS["light_pink"]),
        (3, 1, COLORS["red"]),
        (4, 1, COLORS["wine"]),
        (2, 2, COLORS["red"]),
        (3, 2, COLORS["pink"]),
        (3, 3, COLORS["red"]),
        (3, 4, "#5F8A43"),
        (2, 5, "#5F8A43"),
        (3, 5, "#5F8A43"),
        (4, 6, "#5F8A43"),
    ]

    result = []

    for px, py, color in pixels:

        result.append(
            f'<rect x="{x + px * scale}" '
            f'y="{y + py * scale}" '
            f'width="{scale}" height="{scale}" '
            f'fill="{color}"/>'
        )

    return "".join(result)


def pixel_centipede(x, y, scale=3):

    result = []

    segments = [
        COLORS["wine"],
        COLORS["red"],
        COLORS["pink"],
        COLORS["red"],
        COLORS["wine"],
        COLORS["red"],
        COLORS["pink"],
    ]

    for i, color in enumerate(segments):

        sx = x + i * scale * 5
        sy = y + (i % 2) * scale

        result.append(
            f'<rect x="{sx}" y="{sy}" '
            f'width="{scale * 4}" height="{scale * 3}" '
            f'rx="{scale}" fill="{color}"/>'
        )

        # Small legs
        result.append(
            f'<path d="M{sx + scale} {sy + scale * 3} '
            f'l-{scale} {scale * 2} '
            f'M{sx + scale * 3} {sy + scale * 3} '
            f'l{scale} {scale * 2}" '
            f'stroke="{COLORS["pink"]}" '
            f'stroke-width="1.5" fill="none"/>'
        )

    # Head
    head_x = x + len(segments) * scale * 5

    result.append(
        f'<circle cx="{head_x}" cy="{y + scale}" '
        f'r="{scale * 2}" fill="{COLORS["red"]}"/>'
    )

    return "".join(result)


def svg_header(title, subtitle, height):

    return f"""
    <svg xmlns="http://www.w3.org/2000/svg"
         width="520"
         height="{height}"
         viewBox="0 0 520 {height}">

      <defs>
        <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#110B0E"/>
          <stop offset="100%" stop-color="#090909"/>
        </linearGradient>
      </defs>

      <rect width="520" height="{height}"
            rx="14"
            fill="url(#bg)"
            stroke="{COLORS['border']}"/>

      <rect x="1" y="1" width="518" height="3"
            rx="2" fill="{COLORS['red']}"/>

      {pixel_lily(458, 18, 3)}

      <text x="28" y="29"
            fill="{COLORS['pink']}"
            font-size="10"
            font-family="monospace"
            letter-spacing="2">
        BLOOD GARDEN.exe
      </text>

      <text x="28" y="62"
            fill="{COLORS['text']}"
            font-size="23"
            font-weight="bold"
            font-family="sans-serif">
        {escape(title)}
      </text>

      <text x="28" y="83"
            fill="{COLORS['muted']}"
            font-size="10"
            font-family="monospace">
        {escape(subtitle)}
      </text>
    """


def svg_footer(y):

    return f"""
      <line x1="28" y1="{y}" x2="492" y2="{y}"
            stroke="{COLORS['border']}"
            stroke-width="1"/>

      <text x="28" y="{y + 22}"
            fill="{COLORS['pink']}"
            font-size="9"
            font-family="monospace">
        SYSTEM STATUS // CULTIVATING CODE
      </text>

      {pixel_centipede(360, y + 8, 2)}

    </svg>
    """


def save_svg(filename, content):

    path = ASSETS_DIR / filename

    path.write_text(
        content,
        encoding="utf-8"
    )

    print(f"[SVG] Generated: {path}")

def generate_language_card(language_totals):

    entries = sorted(
        language_totals.items(),
        key=lambda item: item[1],
        reverse=True
    )

    total = sum(language_totals.values())

    if not total:
        entries = [("No data", 1)]
        total = 1

    top = entries[:7]

    if len(entries) > 7:

        others = sum(
            value for _, value in entries[7:]
        )

        top.append(("Other", others))

    height = 370

    svg = svg_header(
        "LANGUAGE SCAN",
        "BYTE DISTRIBUTION // ALL PUBLIC REPOSITORIES",
        height
    )

    y = 125

    for index, (language, amount) in enumerate(top):

        percentage = amount / total * 100

        color = LANGUAGE_COLORS.get(
            language,
            PALETTE[index % len(PALETTE)]
        )

        bar_width = 370 * percentage / 100

        svg += f"""
        <text x="30" y="{y}"
              fill="{COLORS['text']}"
              font-size="12"
              font-family="sans-serif">
            {escape(language)}
        </text>

        <text x="490" y="{y}"
              fill="{COLORS['pink']}"
              font-size="11"
              text-anchor="end"
              font-family="monospace">
            {percentage:.1f}%
        </text>

        <rect x="30" y="{y + 10}"
              width="460" height="8"
              rx="4"
              fill="{COLORS['track']}"/>

        <rect x="30" y="{y + 10}"
              width="{bar_width:.2f}" height="8"
              rx="4"
              fill="{color}"/>
        """

        y += 31

    svg += f"""
    <text x="30" y="347"
          fill="{COLORS['muted']}"
          font-size="9"
          font-family="monospace">
        TOTAL BYTES: {total:,}
    </text>
    """

    svg += svg_footer(360)

    save_svg(
        "language-scan.svg",
        svg
    )

def generate_commit_card(commits_by_language):

    entries = sorted(
        commits_by_language.items(),
        key=lambda item: item[1],
        reverse=True
    )

    total = sum(commits_by_language.values())

    if not entries:
        entries = [("No commits found", 0)]

    top = entries[:7]

    if len(entries) > 7:

        others = sum(
            value for _, value in entries[7:]
        )

        top.append(("Other", others))

    height = 370

    svg = svg_header(
        "COMMIT ACTIVITY",
        "AUTHORED COMMITS // LAST 365 DAYS",
        height
    )

    y = 125

    for index, (language, count) in enumerate(top):

        percentage = (
            count / total * 100
            if total else 0
        )

        color = LANGUAGE_COLORS.get(
            language,
            PALETTE[index % len(PALETTE)]
        )

        bar_width = 370 * percentage / 100

        svg += f"""
        <text x="30" y="{y}"
              fill="{COLORS['text']}"
              font-size="12"
              font-family="sans-serif">
            {escape(language)}
        </text>

        <text x="490" y="{y}"
              fill="{COLORS['pink']}"
              font-size="11"
              text-anchor="end"
              font-family="monospace">
            {count:,} commits
        </text>

        <rect x="30" y="{y + 10}"
              width="460" height="8"
              rx="4"
              fill="{COLORS['track']}"/>

        <rect x="30" y="{y + 10}"
              width="{bar_width:.2f}" height="8"
              rx="4"
              fill="{color}"/>
        """

        y += 31

    svg += f"""
    <text x="30" y="347"
          fill="{COLORS['muted']}"
          font-size="9"
          font-family="monospace">
        TOTAL UNIQUE COMMITS: {total:,}
    </text>
    """

    svg += svg_footer(360)

    save_svg(
        "commit-activity.svg",
        svg
    )
    
def main():

    print("\n")
    print("====================================")
    print("       BLOOD GARDEN.exe")
    print("       GITHUB DATA GENERATOR")
    print("====================================")
    print("\n")

    print("[1/3] Fetching public repositories...")

    repositories = get_public_repositories()

    print(
        f"Found {len(repositories)} public repositories."
    )

    print("\n[2/3] Analyzing languages...")

    language_totals, dominant_languages = (
        get_language_distribution(repositories)
    )

    print("\n[3/3] Analyzing commits...")

    commits_by_language = get_commit_distribution(
        repositories,
        dominant_languages
    )

    print("\nGenerating SVG files...")

    generate_language_card(language_totals)

    generate_commit_card(commits_by_language)

    print("\n")
    print("BLOOD GARDEN.exe — COMPLETE")
    print("SVG cards successfully generated.")
    print("\n")


if __name__ == "__main__":
    main()
