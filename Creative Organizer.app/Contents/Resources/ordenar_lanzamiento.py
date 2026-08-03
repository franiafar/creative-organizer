#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable


STATIC_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MOTION_EXTENSIONS = {".mov", ".mp4", ".m4v", ".gif"}
SUPPORTED_EXTENSIONS = STATIC_EXTENSIONS | MOTION_EXTENSIONS
SYSTEM_JUNK_FILENAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
# India is always split by language, even when a launch contains only one variant.
ALWAYS_SHOW_LANGUAGE_CODES = {"IN"}

STATIC_NAMES = {
    "st",
    "sta",
    "static",
    "still",
    "stills",
}
MOTION_NAMES = {
    "mo",
    "mot",
    "motion",
    "vid",
    "video",
    "videos",
}

COUNTRY_ALIASES = {
    "argentina": ("AR", "Argentina"),
    "australia": ("AU", "Australia"),
    "austria": ("AT", "Austria"),
    "belgium": ("BE", "Belgium"),
    "brazil": ("BR", "Brazil"),
    "brasil": ("BR", "Brazil"),
    "canada": ("CA", "Canada"),
    "chile": ("CL", "Chile"),
    "colombia": ("CO", "Colombia"),
    "costa rica": ("CR", "Costa Rica"),
    "cyprus": ("CY", "Cyprus"),
    "czech republic": ("CZ", "Czech Republic"),
    "denmark": ("DK", "Denmark"),
    "estonia": ("EE", "Estonia"),
    "finland": ("FI", "Finland"),
    "france": ("FR", "France"),
    "germany": ("DE", "Germany"),
    "hungary": ("HU", "Hungary"),
    "india": ("IN", "India"),
    "indonesia": ("ID", "Indonesia"),
    "ireland": ("IE", "Ireland"),
    "italy": ("IT", "Italy"),
    "japan": ("JP", "Japan"),
    "korea": ("KR", "South Korea"),
    "south korea": ("KR", "South Korea"),
    "malaysia": ("MY", "Malaysia"),
    "mexico": ("MX", "Mexico"),
    "netherlands": ("NL", "Netherlands"),
    "new zealand": ("NZ", "New Zealand"),
    "peru": ("PE", "Peru"),
    "philippines": ("PH", "Philippines"),
    "poland": ("PL", "Poland"),
    "singapore": ("SG", "Singapore"),
    "slovenia": ("SI", "Slovenia"),
    "spain": ("ES", "Spain"),
    "sweden": ("SE", "Sweden"),
    "switzerland": ("CH", "Switzerland"),
    "taiwan": ("TW", "Taiwan"),
    "thailand": ("TH", "Thailand"),
    "turkey": ("TR", "Turkey"),
    "united kingdom": ("GB", "United Kingdom"),
    "uk": ("GB", "United Kingdom"),
    "great britain": ("GB", "United Kingdom"),
    "united states": ("US", "United States"),
    "us": ("US", "United States"),
    "vietnam": ("VN", "Vietnam"),
    "viet nam": ("VN", "Vietnam"),
}

LANGUAGE_ALIASES = {
    "arabic": ("AR", "Arabic"),
    "british english": ("EN", "British English"),
    "dutch": ("NL", "Dutch"),
    "english": ("EN", "English"),
    "filipino": ("TL", "Filipino"),
    "french": ("FR", "French"),
    "french canadian": ("FR", "French Canadian"),
    "german": ("DE", "German"),
    "hindi": ("HI", "Hindi"),
    "indonesian": ("ID", "Indonesian"),
    "italian": ("IT", "Italian"),
    "japanese": ("JA", "Japanese"),
    "korean": ("KO", "Korean"),
    "malay": ("MS", "Malay"),
    "portuguese": ("PT", "Portuguese"),
    "roman hindi": ("RO", "Roman Hindi"),
    "spanish": ("ES", "Spanish"),
    "thai": ("TH", "Thai"),
    "traditional chinese": ("ZH", "Traditional Chinese"),
    "turkish": ("TR", "Turkish"),
    "us english": ("EN", "US English"),
    "vietnamese": ("VI", "Vietnamese"),
}

COMBINED_MARKET_ALIASES = {
    "coes": ("CO", "Colombia", "ES", "Spanish"),
    "cres": ("CR", "Costa Rica", "ES", "Spanish"),
    "mxes": ("MX", "Mexico", "ES", "Spanish"),
    "pees": ("PE", "Peru", "ES", "Spanish"),
    "caen": ("CA", "Canada", "EN", "English"),
    "cafr": ("CA", "Canada", "FR", "French Canadian"),
    "gben": ("GB", "United Kingdom", "EN", "British English"),
    "ieen": ("IE", "Ireland", "EN", "British English"),
    "inen": ("IN", "India", "EN", "British English"),
    "inhi": ("IN", "India", "HI", "Hindi"),
    "inro": ("IN", "India", "RO", "Roman Hindi"),
    "usen": ("US", "United States", "EN", "US English"),
}

COUNTRY_CODES = {code for code, _ in COUNTRY_ALIASES.values()}
LANGUAGE_CODES = {code for code, _ in LANGUAGE_ALIASES.values()}

ORGANIZED_FOLDER_RE = re.compile(
    r"^\s*(?P<index>\d+)\s*[-.]?\s*(?P<country>[A-Z]{2})(?:\s+(?P<language>[A-Z]{2}))?(?:\s+(?P<asset>ST|MT))?\s*$"
)


@dataclass
class AssetRecord:
    source: Path
    relative_source: Path
    country_code: str | None = None
    country_name: str | None = None
    language_code: str | None = None
    language_name: str | None = None
    asset_type: str | None = None
    creative_name: str | None = None
    asset_folder_index: int | None = None
    reasons: list[str] = field(default_factory=list)


def normalize(text: str) -> str:
    cleaned = unicodedata.normalize("NFKD", text)
    cleaned = "".join(char for char in cleaned if not unicodedata.combining(char))
    cleaned = cleaned.replace("_", " ")
    cleaned = cleaned.replace("-", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip().lower()


def natural_key(text: str) -> list[object]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", text)]


def is_hidden_part(part: str) -> bool:
    return part.startswith(".")


def iter_launch_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*"), key=lambda item: natural_key(str(item.relative_to(root)))):
        if not path.is_file():
            continue
        if ".launch-organizer" in path.parts:
            continue
        yield path


def iter_supported_files(root: Path) -> Iterable[Path]:
    for path in iter_launch_files(root):
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        yield path


def is_system_junk(path: Path) -> bool:
    return path.name in SYSTEM_JUNK_FILENAMES or path.name.startswith("._")


def parse_clipboard_market_order(text: str) -> list[tuple[str, str | None]]:
    """Extract the first occurrence of each market from a traffic-sheet Country column."""
    markets: list[tuple[str, str | None]] = []
    seen: set[tuple[str, str | None]] = set()
    has_country_header = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        normalized = normalize(line)
        if not line:
            continue
        if normalized in {"country", "manager populates"}:
            has_country_header = has_country_header or normalized == "country"
            continue

        compact = re.sub(r"[^A-Z]", "", line.upper())
        market: tuple[str, str | None] | None = None
        if normalize(compact) in COMBINED_MARKET_ALIASES:
            code, _, language_code, _ = COMBINED_MARKET_ALIASES[normalize(compact)]
            market = (code, language_code)
        elif normalized in COUNTRY_ALIASES:
            code, _ = COUNTRY_ALIASES[normalized]
            market = (code, None)
        else:
            tokens = re.findall(r"\b[A-Z]{2}\b", line.upper())
            if tokens and tokens[0] in COUNTRY_CODES:
                language_code = tokens[1] if len(tokens) > 1 and tokens[1] in LANGUAGE_CODES else None
                market = (tokens[0], language_code)

        if market and market not in seen:
            seen.add(market)
            markets.append(market)

    # Avoid treating unrelated clipboard text as a traffic-sheet order.
    return markets if has_country_header or len(markets) > 1 else []


def clipboard_market_order() -> list[tuple[str, str | None]]:
    if sys.platform != "darwin":
        return []
    try:
        result = subprocess.run(
            ["/usr/bin/pbpaste"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return []
    return parse_clipboard_market_order(result.stdout) if result.returncode == 0 else []


def detect_media_type(parts: list[str], suffix: str) -> tuple[str | None, int | None]:
    for index, part in enumerate(parts):
        normalized = normalize(part)
        if normalized in STATIC_NAMES:
            return "Static", index
        if normalized in MOTION_NAMES:
            return "Motion", index
    if suffix in STATIC_EXTENSIONS:
        return "Static", None
    if suffix in MOTION_EXTENSIONS:
        return "Motion", None
    return None, None


def detect_country_and_language(parts: list[str], file_name: str) -> tuple[str | None, str | None, str | None, str | None]:
    country_code = None
    country_name = None
    language_code = None
    language_name = None

    for part in parts:
        match = ORGANIZED_FOLDER_RE.match(part)
        if match:
            country_code = match.group("country")
            language_code = match.group("language")
            return country_code, country_code, language_code, language_code

    normalized_parts = [normalize(part) for part in parts]
    for normalized in normalized_parts:
        if normalized in COUNTRY_ALIASES and country_code is None:
            country_code, country_name = COUNTRY_ALIASES[normalized]
        if normalized in LANGUAGE_ALIASES and language_code is None:
            language_code, language_name = LANGUAGE_ALIASES[normalized]
        if normalized in COMBINED_MARKET_ALIASES:
            code, name, lang_code, lang_name = COMBINED_MARKET_ALIASES[normalized]
            country_code = country_code or code
            country_name = country_name or name
            language_code = language_code or lang_code
            language_name = language_name or lang_name

    file_tokens = re.findall(r"[A-Z]{4}", file_name.upper())
    for token in file_tokens:
        normalized = normalize(token)
        if normalized in COMBINED_MARKET_ALIASES:
            code, name, lang_code, lang_name = COMBINED_MARKET_ALIASES[normalized]
            country_code = country_code or code
            country_name = country_name or name
            language_code = language_code or lang_code
            language_name = language_name or lang_name
            break

    return country_code, country_name or country_code, language_code, language_name or language_code


def detect_creative_name(parts: list[str], asset_folder_index: int | None) -> str | None:
    ignored = set(STATIC_NAMES | MOTION_NAMES)
    ignored.update({"regions", "reordenado", "review"})

    for index in range(len(parts) - 1, -1, -1):
        part = parts[index]
        normalized = normalize(part)
        if not normalized:
            continue
        if normalized in ignored:
            continue
        if normalized in COUNTRY_ALIASES:
            continue
        if normalized in LANGUAGE_ALIASES:
            continue
        if normalized in COMBINED_MARKET_ALIASES:
            continue
        if ORGANIZED_FOLDER_RE.match(part):
            continue
        if normalized.startswith("regions"):
            continue
        return part.strip()
    return None


def parse_record(root: Path, source: Path) -> AssetRecord:
    relative_source = source.relative_to(root)
    parts = list(relative_source.parts[:-1])
    record = AssetRecord(source=source, relative_source=relative_source)

    asset_type, asset_folder_index = detect_media_type(parts, source.suffix.lower())
    country_code, country_name, language_code, language_name = detect_country_and_language(parts, source.name)
    creative_name = detect_creative_name(parts, asset_folder_index)

    record.asset_type = asset_type
    record.asset_folder_index = asset_folder_index
    record.country_code = country_code
    record.country_name = country_name
    record.language_code = language_code
    record.language_name = language_name
    record.creative_name = creative_name

    if record.country_code is None:
        record.reasons.append("No pude detectar el pais")
    if record.asset_type is None:
        record.reasons.append("No pude detectar si es Static o Motion")
    if record.creative_name is None:
        record.reasons.append("No pude detectar el nombre del creativo")
    return record


def build_market_labels(
    records: list[AssetRecord],
    requested_order: list[tuple[str, str | None]] | None = None,
) -> tuple[dict[tuple[str, str | None], str], dict[tuple[str, str | None], str]]:
    languages_per_country: dict[str, set[str]] = defaultdict(set)
    market_order: list[tuple[str, str | None]] = []
    seen: set[tuple[str, str | None]] = set()

    for record in records:
        if not record.country_code:
            continue
        if record.language_code:
            languages_per_country[record.country_code].add(record.language_code)
        key = (record.country_code, record.language_code)
        if key not in seen:
            seen.add(key)
            market_order.append(key)

    if requested_order:
        ordered_markets: list[tuple[str, str | None]] = []
        for requested_country, requested_language in requested_order:
            for market in market_order:
                country_code, language_code = market
                if country_code != requested_country:
                    continue
                if requested_language is not None and language_code != requested_language:
                    continue
                if market not in ordered_markets:
                    ordered_markets.append(market)
        market_order = ordered_markets + [market for market in market_order if market not in ordered_markets]

    display_map: dict[tuple[str, str | None], str] = {}
    base_map: dict[tuple[str, str | None], str] = {}
    width = max(2, len(str(max(1, len(market_order)))))

    for index, (country_code, language_code) in enumerate(market_order, start=1):
        base_name = f"{index:0{width}d} - {country_code}"
        if language_code and (
            country_code in ALWAYS_SHOW_LANGUAGE_CODES
            or len(languages_per_country[country_code]) > 1
        ):
            base_name = f"{base_name} {language_code}"
        base_map[(country_code, language_code)] = base_name
        display_map[(country_code, language_code)] = base_name

    return base_map, display_map


def destination_for_record(
    root: Path,
    record: AssetRecord,
    base_map: dict[tuple[str, str | None], str],
    asset_types_by_market: dict[tuple[str, str | None], set[str]],
) -> Path | None:
    if not (record.country_code and record.asset_type and record.creative_name):
        return None

    key = (record.country_code, record.language_code)
    market_folder = base_map[key]
    asset_types = asset_types_by_market[key]
    if asset_types == {"Static"}:
        market_folder = f"{market_folder} ST"
        relative_destination = Path(market_folder) / record.creative_name / record.source.name
    elif asset_types == {"Motion"}:
        market_folder = f"{market_folder} MT"
        relative_destination = Path(market_folder) / record.creative_name / record.source.name
    else:
        relative_destination = Path(market_folder) / record.asset_type / record.creative_name / record.source.name
    return root / relative_destination


def ensure_unique_destination(source: Path, destination: Path) -> Path:
    if source == destination:
        return destination
    if not destination.exists():
        return destination
    stem = destination.stem
    suffix = destination.suffix
    counter = 2
    while True:
        candidate = destination.with_name(f"{stem} ({counter}){suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def remove_empty_directories(root: Path) -> None:
    paths = sorted((path for path in root.rglob("*") if path.is_dir()), key=lambda item: len(item.parts), reverse=True)
    for path in paths:
        if path.name == ".launch-organizer":
            continue
        try:
            next(path.iterdir())
        except StopIteration:
            path.rmdir()


def remove_system_junk_files(root: Path) -> None:
    for path in iter_launch_files(root):
        if is_system_junk(path):
            path.unlink()


def clear_old_undo_records(metadata_dir: Path) -> None:
    """Keep only the one undo record for the most recent organization."""
    for pattern in ("plan-*.json", "undo-*.json", "undo-applied-*.json"):
        for path in metadata_dir.glob(pattern):
            path.unlink()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def build_plan(
    root: Path,
    requested_order: list[tuple[str, str | None]] | None = None,
) -> tuple[list[AssetRecord], list[dict], list[AssetRecord], dict]:
    all_files = list(iter_launch_files(root))
    records = [parse_record(root, file_path) for file_path in all_files if file_path.suffix.lower() in SUPPORTED_EXTENSIONS]
    resolved = [record for record in records if not record.reasons]
    unresolved = [record for record in records if record.reasons]

    base_map, _ = build_market_labels(resolved, requested_order)
    asset_types_by_market: dict[tuple[str, str | None], set[str]] = defaultdict(set)
    for record in resolved:
        asset_types_by_market[(record.country_code, record.language_code)].add(record.asset_type)

    moves: list[dict] = []
    for record in resolved:
        destination = destination_for_record(root, record, base_map, asset_types_by_market)
        if destination is None:
            continue
        moves.append(
            {
                "assetType": record.asset_type,
                "creativeName": record.creative_name,
                "marketKey": " ".join(part for part in [record.country_code, record.language_code] if part),
                "relativeSource": record.relative_source.as_posix(),
                "relativeDestination": destination.relative_to(root).as_posix(),
                "source": str(record.source),
                "destination": str(destination),
            }
        )

    unresolved_sources = {record.source for record in unresolved}
    other_files = [
        file_path
        for file_path in all_files
        if not is_system_junk(file_path)
        and (file_path.suffix.lower() not in SUPPORTED_EXTENSIONS or file_path in unresolved_sources)
    ]
    for file_path in other_files:
        moves.append(
            {
                "assetType": "Other",
                "creativeName": "Otros",
                "marketKey": "",
                "relativeSource": file_path.relative_to(root).as_posix(),
                "relativeDestination": (Path("Otros") / file_path.name).as_posix(),
                "source": str(file_path),
                "destination": str(root / "Otros" / file_path.name),
            }
        )

    summary = {
        "totalFiles": len(all_files),
        "resolvedFiles": len(resolved),
        "unresolvedFiles": 0,
        "otherFiles": len(other_files),
        "marketCount": len({record.country_code for record in resolved if record.country_code}),
        "markets": list(dict.fromkeys(country_code for country_code, _ in base_map)),
        "clipboardOrderUsed": bool(requested_order),
        "systemJunk": [file_path.relative_to(root).as_posix() for file_path in all_files if is_system_junk(file_path)],
    }
    return records, moves, unresolved, summary


def print_summary(root: Path, summary: dict, moves: list[dict], unresolved: list[AssetRecord]) -> None:
    print()
    print(f"Carpeta: {root}")
    print(f"Archivos detectados: {summary['totalFiles']}")
    print(f"Archivos listos para mover: {summary['resolvedFiles']}")
    print(f"Archivos sin resolver: {summary['unresolvedFiles']}")
    print(f"Mercados detectados: {', '.join(summary['markets']) or 'ninguno'}")

    if moves:
        print()
        print("Primeros destinos:")
        shown = set()
        for move in moves:
            destination = move["relativeDestination"]
            preview = "/".join(destination.split("/")[:3])
            if preview in shown:
                continue
            shown.add(preview)
            print(f"  - {preview}")
            if len(shown) >= 8:
                break

    if summary["otherFiles"]:
        print(f"Archivos enviados a Otros: {summary['otherFiles']}")


def apply_plan(root: Path, moves: list[dict], unresolved: list[AssetRecord], system_junk: list[str]) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    metadata_dir = root / ".launch-organizer"
    metadata_dir.mkdir(exist_ok=True)
    clear_old_undo_records(metadata_dir)
    undo_path = metadata_dir / "undo-last.json"

    applied_moves: list[dict] = []
    for move in moves:
        source = root / move["relativeSource"]
        destination = ensure_unique_destination(source, root / move["relativeDestination"])
        if source == destination:
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        applied_moves.append(
            {
                "from": move["relativeSource"],
                "to": destination.relative_to(root).as_posix(),
            }
        )

    remove_system_junk_files(root)

    remove_empty_directories(root)

    write_json(
        undo_path,
        {
            "createdAt": stamp,
            "root": str(root),
            "moves": applied_moves,
        },
    )
    return undo_path


def undo_last(root: Path) -> Path | None:
    metadata_dir = root / ".launch-organizer"
    undo_path = metadata_dir / "undo-last.json"
    if not undo_path.exists():
        return None

    payload = json.loads(undo_path.read_text(encoding="utf-8"))
    moves = payload.get("moves", [])
    for move in reversed(moves):
        source = root / move["to"]
        destination = root / move["from"]
        if not source.exists():
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))

    remove_system_junk_files(root)
    remove_empty_directories(root)
    undo_path.unlink()
    return undo_path


def clean_dragged_path(raw_value: str) -> str:
    value = raw_value.strip()
    if value.startswith("'") and value.endswith("'"):
        value = value[1:-1]
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    return value.replace("\\ ", " ")


def build_summary_message(root: Path, summary: dict, unresolved: list[AssetRecord]) -> str:
    lines = [
        f"Carpeta: {root.name}",
        f"Archivos detectados: {summary['totalFiles']}",
        f"Listos para mover: {summary['resolvedFiles']}",
        f"Sin resolver: {summary['unresolvedFiles']}",
        f"Mercados detectados: {summary['marketCount']}",
    ]
    if unresolved:
        lines.append("")
        lines.append("Hay archivos para revisar.")
    return "\n".join(lines)


def run_macos_dialog(script: str, *arguments: str) -> str | None:
    """Run a native macOS dialog without creating a second app window."""
    try:
        result = subprocess.run(
            ["/usr/bin/osascript", "-e", script, *arguments],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def display_macos_message(message: str, title: str = "Organizador de Lanzamientos") -> None:
    run_macos_dialog(
        '''on run argv
display dialog (item 1 of argv) buttons {"Cerrar"} default button "Cerrar" with title (item 2 of argv)
end run''',
        message,
        title,
    )


def gui_mode() -> int | None:
    if sys.platform != "darwin":
        return None

    folder_path = run_macos_dialog(
        '''try
set selectedFolder to choose folder with prompt "Elegi la carpeta del lanzamiento" default location (path to desktop folder)
return POSIX path of selectedFolder
on error number -128
return ""
end try'''
    )
    if not folder_path:
        return 0

    root = Path(folder_path).resolve()
    if not root.is_dir():
        display_macos_message("No encontre esa carpeta. Intenta de nuevo.")
        return 1

    action = run_macos_dialog(
        '''on run argv
set folderName to item 1 of argv
set response to display dialog "Carpeta elegida: " & folderName & "\n\nQue queres hacer?" buttons {"Cancelar", "Preview", "Undo", "Ordenar"} default button "Ordenar" cancel button "Cancelar" with title "Organizador de Lanzamientos"
return button returned of response
end run''',
        root.name,
    )
    if not action:
        return 0

    if action == "Undo":
        confirmation = run_macos_dialog(
            '''set response to display dialog "Esto revierte la ultima organizacion hecha en esta carpeta." buttons {"Cancelar", "Deshacer"} default button "Deshacer" cancel button "Cancelar" with title "Deshacer organizacion"
return button returned of response'''
        )
        if confirmation != "Deshacer":
            return 0
        undone = undo_last(root)
        if undone is None:
            display_macos_message("No encontre una organizacion anterior para deshacer.", "Sin Undo")
            return 0
        display_macos_message("Undo aplicado.", "Listo")
        return 0

    _, moves, unresolved, summary = build_plan(root, clipboard_market_order())
    message = build_summary_message(root, summary, unresolved)
    if action == "Preview":
        display_macos_message(message + "\n\nNo movi ningun archivo.", "Preview")
        return 0

    confirmation = run_macos_dialog(
        '''on run argv
set response to display dialog (item 1 of argv) buttons {"Cancelar", "Ordenar"} default button "Ordenar" cancel button "Cancelar" with title "Confirmar organizacion"
return button returned of response
end run''',
        message + "\n\nVoy a mover y renombrar archivos dentro de esta carpeta. Queres seguir?",
    )
    if confirmation != "Ordenar":
        return 0

    apply_plan(root, moves, unresolved, summary["systemJunk"])
    final_message = "Listo. Reordene la carpeta sin duplicar archivos."
    if unresolved:
        final_message += f"\nQuedaron {len(unresolved)} archivos para revisar."
    display_macos_message(final_message, "Organizacion terminada")
    return 0


def ask_root_path() -> Path:
    while True:
        raw_value = input("Arrastra la carpeta del lanzamiento aca y apreta Enter:\n> ")
        root = Path(clean_dragged_path(raw_value)).expanduser()
        if root.exists() and root.is_dir():
            return root.resolve()
        print("No encontre esa carpeta. Probemos de nuevo.\n")


def interactive_mode() -> int:
    print("Organizador de lanzamientos")
    print("---------------------------")
    gui_result = gui_mode()
    if gui_result is not None:
        return gui_result

    root = ask_root_path()
    action = input("\nElegi una accion: [A]plicar, [P]review, [U]ndo ultima corrida (default A)\n> ").strip().lower() or "a"

    if action.startswith("u"):
        undone = undo_last(root)
        print()
        if undone is None:
            print("No encontre un undo para esa carpeta.")
            return 1
        print(f"Undo aplicado. Archivo usado: {undone}")
        return 0

    _, moves, unresolved, summary = build_plan(root, clipboard_market_order())
    print_summary(root, summary, moves, unresolved)

    if action.startswith("p"):
        print("\nPreview listo. No movi nada.")
        return 0

    confirm = input("\nVoy a mover y renombrar estos archivos. Seguir? [y/N]\n> ").strip().lower()
    if confirm != "y":
        print("Cancelado.")
        return 0

    undo_path = apply_plan(root, moves, unresolved, summary["systemJunk"])
    print()
    print("Listo. Reordene la carpeta sin duplicar archivos.")
    print(f"Undo guardado en: {undo_path}")
    if unresolved:
        print(f"Atencion: quedaron {len(unresolved)} archivos para revisar.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reordena carpetas de lanzamientos sin duplicar archivos.")
    parser.add_argument("--root", help="Carpeta del lanzamiento a ordenar")
    parser.add_argument("--preview", action="store_true", help="Muestra el plan sin mover nada")
    parser.add_argument("--apply", action="store_true", help="Aplica el plan")
    parser.add_argument("--undo", action="store_true", help="Revierte la ultima corrida")
    parser.add_argument("--interactive", action="store_true", help="Modo interactivo")
    args = parser.parse_args(argv)

    if args.interactive or not any([args.root, args.preview, args.apply, args.undo]):
        return interactive_mode()

    if not args.root:
        print("Falta --root", file=sys.stderr)
        return 2

    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"No existe la carpeta: {root}", file=sys.stderr)
        return 2

    if args.undo:
        undone = undo_last(root)
        if undone is None:
            print("No encontre un undo para esa carpeta.", file=sys.stderr)
            return 1
        print(undone)
        return 0

    _, moves, unresolved, summary = build_plan(root, clipboard_market_order())
    print_summary(root, summary, moves, unresolved)

    if args.preview or not args.apply:
        return 0

    undo_path = apply_plan(root, moves, unresolved, summary["systemJunk"])
    print()
    print(f"Undo guardado en: {undo_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
