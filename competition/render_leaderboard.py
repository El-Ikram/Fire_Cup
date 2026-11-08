# competition/render_leaderboard.py

import csv
from pathlib import Path
from datetime import datetime, timezone
from html import escape

ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = ROOT / "docs" / "leaderboard.csv"
MD_PATH = ROOT / "leaderboard" / "leaderboard.md"

REQUIRED_COLUMNS = {
    "team",
    "score",
    "timestamp_utc"
}


def read_rows():

    if not CSV_PATH.exists():
        return []

    with CSV_PATH.open("r", encoding="utf-8") as file:

        reader = csv.DictReader(file)

        if not REQUIRED_COLUMNS.issubset(reader.fieldnames or []):
            raise ValueError(
                "leaderboard.csv must contain columns: "
                "team, score, timestamp_utc"
            )

        rows = []

        for row in reader:

            team = (row.get("team") or "").strip()
            score = row.get("score")
            timestamp = row.get("timestamp_utc")

            if not team:
                continue

            try:
                score = float(score)
            except (TypeError, ValueError):
                continue

            rows.append({
                "team": team,
                "score": score,
                "timestamp_utc": timestamp
            })

    return rows


def sort_rows(rows):

    # Primary: mAP@50:95 DESC
    # Secondary: earliest submission wins ties

    return sorted(
        rows,
        key=lambda row: (
            -row["score"],
            row["timestamp_utc"]
        )
    )


def generate_markdown(rows):

    now = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )

    lines = [
        "# Fire Detection Competition Leaderboard\n\n",
        f"Last updated: {now}\n\n",
        "| Rank | Team | mAP@50:95 | Date |\n",
        "|---:|---|---:|---|\n"
    ]

    for rank, row in enumerate(rows, start=1):

        lines.append(
            f"| {rank} | {escape(row['team'])} | "
            f"{row['score']:.8f} | "
            f"{row['timestamp_utc']} |\n"
        )

    MD_PATH.parent.mkdir(parents=True, exist_ok=True)

    MD_PATH.write_text(
        "".join(lines),
        encoding="utf-8"
    )


def main():

    rows = read_rows()
    rows = sort_rows(rows)

    generate_markdown(rows)


if __name__ == "__main__":
    main()
