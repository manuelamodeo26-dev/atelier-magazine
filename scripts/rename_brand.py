from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
updated = text.replace("THE ATELIER VERSE", "ATELIER")
updated = updated.replace("The Atelier Verse", "ATELIER")

if updated != text:
    path.write_text(updated, encoding="utf-8")
