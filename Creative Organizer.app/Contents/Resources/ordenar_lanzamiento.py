#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


STATIC_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MOTION_EXTENSIONS = {".mov", ".mp4", ".m4v", ".gif"}
SUPPORTED_EXTENSIONS = STATIC_EXTENSIONS | MOTION_EXTENSIONS
ALWAYS_SHOW_LANGUAGE_CODES = {"IN"}

STATIC_NAMES = {"st", "sta", "static", "still", "stills", "image", "images"}
MOTION_NAMES = {"mo", "mot", "motion", "vid", "video", "videos"}
PLATFORM_ALIASES = {
    "meta": "Meta",
    "facebook": "Meta",
    "instagram": "Meta",
    "tiktok": "TikTok",
    "tik tok": "TikTok",
    "tt": "TikTok",
}
OUT_OF_SCOPE_PLATFORMS = {
    "youtube",
    "you tube",
    "yt",
    "linkedin",
    "snapchat",
    "pinterest",
    "google",
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
    "phillipines": ("PH", "Philippines"),
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
    "caen": ("CA", "Canada", "EN", "English"),
    "cafr": ("CA", "Canada", "FR", "French Canadian"),
    "inen": ("IN", "India", "EN", "British English"),
    "inhi": ("IN", "India", "HI", "Hindi"),
    "inhr": ("IN", "India", "RO", "Roman Hindi"),
    "inro": ("IN", "India", "RO", "Roman Hindi"),
    "uken": ("GB", "United Kingdom", "EN", "British English"),
}

COUNTRY_CODES = {value[0] for value in COUNTRY_ALIASES.values()}
LANGUAGE_CODES = {value[0] for value in LANGUAGE_ALIASES.values()}
COUNTRY_NAMES_BY_CODE = {value[0]: value[1] for value in COUNTRY_ALIASES.values()}
LANGUAGE_NAMES_BY_CODE = {value[0]: value[1] for value in LANGUAGE_ALIASES.values()}
MARKET_CODE_ALIASES = {"UK": "GB"}

ORGANIZED_FOLDER_RE = re.compile(
    r"^\s*(?P<index>\d+)\s*-\s*(?P<country>[A-Z]{2})"
    r"(?:\s+(?P<language>(?!(?:Static|Motion|St|Mt)(?:\s|$))[A-Z]{2}))?"
    r"(?:\s*-\s*(?P<asset>Static|Motion|St|Mt))?\s*$",
    re.IGNORECASE,
)
GENERIC_WRAPPER_RE = re.compile(
    r"^(?:motion|mot|video|static|stat|still|image|img|export|exports|delivery|deliverables)\s*\d*$"
)
ASPECT_RE = re.compile(r"^\d{1,2}\s*[x:]\s*\d{1,2}$", re.IGNORECASE)
RESOLUTION_RE = re.compile(r"^\d{3,5}\s*x\s*\d{3,5}(?:\s*px)?$", re.IGNORECASE)
DURATION_RE = re.compile(r"^\d+(?:\.\d+)?\s*(?:s|sec|secs|seconds)$", re.IGNORECASE)
DATE_RE = re.compile(r"^(?:\d{4}[-.]\d{1,2}[-.]\d{1,2}|\d{1,2}[-.]\d{1,2}[-.]\d{2,4})$")
PRODUCTION_ID_RE = re.compile(r"^(?:\d{3,}|(?:id|pid|job|v)\s*[- ]?\d+)$", re.IGNORECASE)


@dataclass
class AssetRecord:
    source: Path
    relative_source: Path
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    language_code: Optional[str] = None
    language_name: Optional[str] = None
    platform: Optional[str] = None
    scope: str = "unresolved"
    asset_type: Optional[str] = None
    creative_name: Optional[str] = None
    creative_path: List[str] = field(default_factory=list)
    semantic_source_path: List[str] = field(default_factory=list)
    ignored_metadata: List[str] = field(default_factory=list)
    evidence: Dict[str, object] = field(default_factory=dict)
    confidence: str = "low"
    reasons: List[str] = field(default_factory=list)
    existing_market_index: Optional[int] = None
    destination: Optional[Path] = None


class OrganizationError(RuntimeError):
    """A concise, user-facing error while applying an organization."""


def normalize(text: str) -> str:
    cleaned = unicodedata.normalize("NFKD", text)
    cleaned = "".join(char for char in cleaned if not unicodedata.combining(char))
    cleaned = cleaned.replace("_", " ").replace("-", " ")
    return re.sub(r"\s+", " ", cleaned).strip().lower()


def natural_key(text: str) -> List[object]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", text)]


def market_from_compact_token(token: str) -> Optional[Tuple[str, str, str, str]]:
    compact = re.sub(r"[^A-Z]", "", token.upper()).lower()
    if compact in COMBINED_MARKET_ALIASES:
        return COMBINED_MARKET_ALIASES[compact]
    if len(compact) != 4:
        return None
    country_code = MARKET_CODE_ALIASES.get(compact[:2].upper(), compact[:2].upper())
    language_code = compact[2:].upper()
    if country_code not in COUNTRY_CODES or language_code not in LANGUAGE_CODES:
        return None
    return (
        country_code,
        COUNTRY_NAMES_BY_CODE[country_code],
        language_code,
        LANGUAGE_NAMES_BY_CODE[language_code],
    )


def country_code_from_token(token: str) -> Optional[str]:
    normalized = normalize(token)
    if normalized in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[normalized][0]
    compact = re.sub(r"[^A-Z]", "", token.upper())
    canonical = MARKET_CODE_ALIASES.get(compact, compact)
    if len(canonical) == 2 and canonical in COUNTRY_CODES:
        return canonical
    return None


def language_code_from_token(token: str) -> Optional[str]:
    normalized = normalize(token)
    if normalized in LANGUAGE_ALIASES:
        return LANGUAGE_ALIASES[normalized][0]
    compact = re.sub(r"[^A-Z]", "", token.upper())
    if len(compact) == 2 and compact in LANGUAGE_CODES:
        return compact
    return None


def iter_launch_files(root: Path) -> Iterable[Path]:
    paths = sorted(root.rglob("*"), key=lambda item: natural_key(str(item.relative_to(root))))
    for path in paths:
        if path.is_file() and ".launch-organizer" not in path.parts:
            yield path


def iter_supported_files(root: Path) -> Iterable[Path]:
    for path in iter_launch_files(root):
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def parse_clipboard_market_order(text: str) -> List[Tuple[str, Optional[str]]]:
    markets = []  # type: List[Tuple[str, Optional[str]]]
    seen = set()  # type: Set[Tuple[str, Optional[str]]]
    has_header = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        normalized = normalize(line)
        if not line:
            continue
        if normalized in {"country", "manager populates"}:
            has_header = has_header or normalized == "country"
            continue
        compact_market = market_from_compact_token(line)
        market = None  # type: Optional[Tuple[str, Optional[str]]]
        if compact_market:
            market = (compact_market[0], compact_market[2])
        elif normalized in COUNTRY_ALIASES:
            market = (COUNTRY_ALIASES[normalized][0], None)
        else:
            codes = re.findall(r"\b[A-Z]{2}\b", line.upper())
            if codes:
                country = MARKET_CODE_ALIASES.get(codes[0], codes[0])
                if country in COUNTRY_CODES:
                    language = codes[1] if len(codes) > 1 and codes[1] in LANGUAGE_CODES else None
                    market = (country, language)
        if market and market not in seen:
            seen.add(market)
            markets.append(market)
    return markets if has_header or len(markets) > 1 else []


def clipboard_market_order() -> List[Tuple[str, Optional[str]]]:
    if sys.platform != "darwin":
        return []
    try:
        result = subprocess.run(["/usr/bin/pbpaste"], check=False, capture_output=True, text=True)
    except OSError:
        return []
    return parse_clipboard_market_order(result.stdout) if result.returncode == 0 else []


def filename_fields(file_name: str) -> List[str]:
    return [field.strip() for field in Path(file_name).stem.split("_") if field.strip()]


def media_from_token(token: str) -> Optional[str]:
    normalized = normalize(token)
    if normalized in STATIC_NAMES:
        return "Static"
    if normalized in MOTION_NAMES:
        return "Motion"
    return None


def platform_from_token(token: str) -> Optional[str]:
    return PLATFORM_ALIASES.get(normalize(token))


def out_of_scope_platform_from_token(token: str) -> Optional[str]:
    normalized = normalize(token)
    return token.strip() if normalized in OUT_OF_SCOPE_PLATFORMS else None


def is_technical_token(token: str) -> bool:
    normalized = normalize(token)
    compact = re.sub(r"[^A-Z]", "", token.upper())
    return bool(
        not normalized
        or media_from_token(token)
        or platform_from_token(token)
        or out_of_scope_platform_from_token(token)
        or market_from_compact_token(token)
        or country_code_from_token(token)
        or language_code_from_token(token)
        or ASPECT_RE.fullmatch(token.strip())
        or RESOLUTION_RE.fullmatch(token.strip())
        or DURATION_RE.fullmatch(token.strip())
        or DATE_RE.fullmatch(token.strip())
        or PRODUCTION_ID_RE.fullmatch(token.strip())
        or re.fullmatch(r"(?:static|motion|still|video)\s*\d+", normalized)
        or (len(compact) >= 6 and any(char.isdigit() for char in compact))
    )


def descriptor_fields(file_name: str) -> List[str]:
    runs = []  # type: List[List[str]]
    current = []  # type: List[str]
    for token in filename_fields(file_name):
        if is_technical_token(token):
            if current:
                runs.append(current)
                current = []
        else:
            current.append(token.strip())
    if current:
        runs.append(current)
    if not runs:
        return []
    return max(runs, key=lambda run: (len(run), sum(len(item) for item in run)))


def humanize_descriptor(tokens: List[str]) -> str:
    return " ".join(re.sub(r"\s+", " ", token.replace("-", " ")).strip() for token in tokens).strip()


def organized_folder(part: str) -> Optional[re.Match]:
    return ORGANIZED_FOLDER_RE.fullmatch(part)


def is_technical_path_part(part: str) -> bool:
    normalized = normalize(part)
    return bool(
        not normalized
        or normalized == "regions"
        or normalized.startswith("regions ")
        or media_from_token(part)
        or platform_from_token(part)
        or out_of_scope_platform_from_token(part)
        or market_from_compact_token(part)
        or normalized in COUNTRY_ALIASES
        or normalized in LANGUAGE_ALIASES
        or organized_folder(part)
        or GENERIC_WRAPPER_RE.fullmatch(normalized)
        or ASPECT_RE.fullmatch(part.strip())
        or RESOLUTION_RE.fullmatch(part.strip())
        or DURATION_RE.fullmatch(part.strip())
        or DATE_RE.fullmatch(part.strip())
        or PRODUCTION_ID_RE.fullmatch(part.strip())
    )


def detect_platform(parts: List[str], file_name: str) -> Tuple[Optional[str], str, List[str]]:
    path_platforms = [platform_from_token(part) for part in parts if platform_from_token(part)]
    path_out = [out_of_scope_platform_from_token(part) for part in parts if out_of_scope_platform_from_token(part)]
    filename_platforms = [platform_from_token(field) for field in filename_fields(file_name) if platform_from_token(field)]
    filename_out = [
        out_of_scope_platform_from_token(field)
        for field in filename_fields(file_name)
        if out_of_scope_platform_from_token(field)
    ]
    evidence = []  # type: List[str]
    if path_platforms:
        evidence.append("source path: " + path_platforms[0])
        if filename_platforms and filename_platforms[0] != path_platforms[0]:
            evidence.append("conflicting filename: " + filename_platforms[0])
        return path_platforms[0], "supported", evidence
    if path_out:
        evidence.append("source path: " + str(path_out[0]))
        return str(path_out[0]), "out_of_scope", evidence
    if filename_platforms:
        evidence.append("anchored filename field: " + filename_platforms[0])
        return filename_platforms[0], "supported", evidence
    if filename_out:
        evidence.append("anchored filename field: " + str(filename_out[0]))
        return str(filename_out[0]), "out_of_scope", evidence
    return None, "unresolved", evidence


def detect_market(parts: List[str], file_name: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[int], List[str]]:
    country = None
    language = None
    existing_index = None
    evidence = []  # type: List[str]
    for part in parts:
        match = organized_folder(part)
        if match:
            country = MARKET_CODE_ALIASES.get(match.group("country").upper(), match.group("country").upper())
            language = match.group("language")
            language = language.upper() if language else None
            existing_index = int(match.group("index"))
            evidence.append("organized source folder: " + part)
            break
    for part in parts:
        compact = market_from_compact_token(part)
        if compact:
            if country is None:
                country = compact[0]
                language = compact[2]
                evidence.append("source path market: " + part)
            continue
        normalized = normalize(part)
        if country is None:
            path_country = country_code_from_token(part)
            if path_country:
                country = path_country
                evidence.append("source path country: " + part)
                continue
        if country is not None and language is None:
            if normalized in LANGUAGE_ALIASES:
                language = LANGUAGE_ALIASES[normalized][0]
                evidence.append("source path language: " + part)
            elif part.isupper() and language_code_from_token(part):
                language = language_code_from_token(part)
                evidence.append("source path language code: " + part)
    for field in filename_fields(file_name):
        compact = market_from_compact_token(field)
        if compact:
            if country is None:
                country = compact[0]
                language = compact[2]
                evidence.append("anchored filename market: " + field)
            elif country != compact[0] or (language and language != compact[2]):
                evidence.append("conflicting filename market ignored: " + field)
            elif language is None:
                language = compact[2]
            break
    country_name = COUNTRY_NAMES_BY_CODE.get(country) if country else None
    language_name = LANGUAGE_NAMES_BY_CODE.get(language) if language else None
    return country, country_name, language, language_name, existing_index, evidence


def detect_media(parts: List[str], suffix: str, file_name: str) -> Tuple[Optional[str], List[str]]:
    evidence = []  # type: List[str]
    for part in parts:
        media = media_from_token(part)
        if media:
            evidence.append("source path media folder: " + part)
            extension_media = "Static" if suffix in STATIC_EXTENSIONS else "Motion" if suffix in MOTION_EXTENSIONS else None
            if extension_media and extension_media != media:
                evidence.append("conflicting extension ignored: " + suffix)
            return media, evidence
        match = organized_folder(part)
        if match and match.group("asset"):
            raw_asset = normalize(match.group("asset"))
            media = "Static" if raw_asset in {"st", "static"} else "Motion"
            evidence.append("organized market suffix: " + match.group("asset"))
            return media, evidence
    for field in filename_fields(file_name):
        media = media_from_token(field)
        if media:
            evidence.append("anchored filename media: " + field)
            return media, evidence
    if suffix in STATIC_EXTENSIONS:
        return "Static", ["file extension: " + suffix]
    if suffix in MOTION_EXTENSIONS:
        return "Motion", ["file extension: " + suffix]
    return None, evidence


def enrich_semantic_path(source_semantic: List[str], descriptors: List[str]) -> List[str]:
    if not source_semantic:
        label = humanize_descriptor(descriptors)
        return [label] if label else []
    result = list(source_semantic)
    if not descriptors:
        return result
    descriptor_words = []  # type: List[str]
    for field in descriptors:
        descriptor_words.extend(normalize(field).split())
    leaf_words = normalize(result[-1]).split()
    if len(descriptor_words) < len(leaf_words) or descriptor_words[: len(leaf_words)] != leaf_words:
        return result
    extras = descriptors
    consumed = 0
    while extras and consumed < len(leaf_words):
        consumed += len(normalize(extras[0]).split())
        extras = extras[1:]
    if consumed == len(leaf_words) and extras:
        suffix = humanize_descriptor(extras)
        if suffix and normalize(suffix) not in normalize(result[-1]):
            result[-1] = result[-1] + " - " + suffix
    return result


def parse_record(root: Path, source: Path) -> AssetRecord:
    relative = source.relative_to(root)
    parts = list(relative.parts[:-1])
    record = AssetRecord(source=source, relative_source=relative)

    platform, scope, platform_evidence = detect_platform(parts, source.name)
    record.platform = platform
    record.scope = scope
    record.evidence["platform"] = platform_evidence
    if scope == "out_of_scope":
        record.confidence = "high"
        return record

    country, country_name, language, language_name, existing_index, market_evidence = detect_market(parts, source.name)
    record.country_code = country
    record.country_name = country_name
    record.language_code = language
    record.language_name = language_name
    record.existing_market_index = existing_index
    record.evidence["market"] = market_evidence
    if country is None:
        record.reasons.append("No market evidence")
    if platform is None:
        if existing_index is None:
            record.reasons.append("No supported Meta or TikTok platform evidence")
        else:
            record.evidence["platform"] = ["already organized destination; no platform level required"]

    asset_type, media_evidence = detect_media(parts, source.suffix.lower(), source.name)
    record.asset_type = asset_type
    record.evidence["mediaType"] = media_evidence
    if asset_type is None:
        record.reasons.append("No Static or Motion evidence")

    semantic = []  # type: List[str]
    ignored = []  # type: List[str]
    for part in parts:
        if is_technical_path_part(part):
            ignored.append(part)
        else:
            semantic.append(part.strip())
    descriptors = descriptor_fields(source.name)
    record.semantic_source_path = semantic
    record.ignored_metadata = ignored
    record.evidence["semanticPath"] = ["source folder: " + item for item in semantic]
    record.evidence["filenameDescriptors"] = descriptors
    record.creative_path = enrich_semantic_path(semantic, descriptors)
    record.creative_name = " / ".join(record.creative_path) if record.creative_path else None
    if not record.creative_path:
        record.reasons.append("No safe semantic creative path")

    if not record.reasons:
        record.scope = "supported"
        record.confidence = "high" if semantic else "medium"
    else:
        record.scope = "unresolved"
        record.confidence = "low"
    return record


def build_market_labels(
    records: List[AssetRecord],
    requested_order: Optional[List[Tuple[str, Optional[str]]]] = None,
) -> Tuple[Dict[Tuple[str, Optional[str]], str], Dict[Tuple[str, Optional[str]], str]]:
    markets = sorted(
        {(record.country_code, record.language_code) for record in records if record.country_code},
        key=lambda market: (str(market[0]), str(market[1] or "")),
    )
    existing_indexes = defaultdict(set)  # type: Dict[Tuple[str, Optional[str]], Set[int]]
    for record in records:
        key = (record.country_code, record.language_code)
        if record.country_code and record.existing_market_index is not None:
            existing_indexes[key].add(record.existing_market_index)

    preserve_existing = bool(markets) and all(len(existing_indexes.get(market, set())) == 1 for market in markets)
    if preserve_existing:
        markets.sort(key=lambda market: (next(iter(existing_indexes[market])), str(market[0]), str(market[1] or "")))
    elif requested_order:
        ordered = []  # type: List[Tuple[str, Optional[str]]]
        for requested_country, requested_language in requested_order:
            matching = [
                market
                for market in markets
                if market[0] == requested_country
                and (requested_language is None or market[1] == requested_language)
            ]
            for market in matching:
                if market not in ordered:
                    ordered.append(market)
        markets = ordered + [market for market in markets if market not in ordered]

    languages_by_country = defaultdict(set)  # type: Dict[str, Set[Optional[str]]]
    for country, language in markets:
        if country:
            languages_by_country[country].add(language)

    labels = {}  # type: Dict[Tuple[str, Optional[str]], str]
    for position, market in enumerate(markets, start=1):
        country, language = market
        index = next(iter(existing_indexes[market])) if preserve_existing else position
        label = str(index) + " - " + str(country)
        if language and (country in ALWAYS_SHOW_LANGUAGE_CODES or len(languages_by_country[country]) > 1):
            label += " " + language
        labels[market] = label
    return labels, dict(labels)


def destination_for_record(
    root: Path,
    record: AssetRecord,
    base_map: Dict[Tuple[str, Optional[str]], str],
    asset_types_by_market: Dict[Tuple[str, Optional[str]], Set[str]],
    include_platform: bool = False,
) -> Optional[Path]:
    if not (record.country_code and record.asset_type and record.creative_path):
        return None
    key = (record.country_code, record.language_code)
    market_folder = base_map[key]
    asset_types = asset_types_by_market[key]
    parts = [market_folder]  # type: List[str]
    if len(asset_types) == 1:
        parts[0] += " - " + record.asset_type
    else:
        parts.append(record.asset_type)
    if include_platform and record.platform:
        parts.append(record.platform)
    parts.extend(record.creative_path)
    parts.append(record.source.name)
    return root.joinpath(*parts)


def move_preview(record: AssetRecord, root: Path) -> Dict[str, object]:
    destination = record.destination
    assert destination is not None
    return {
        "action": "stay" if destination == record.source else "move",
        "assetType": record.asset_type,
        "confidence": record.confidence,
        "creativeName": record.creative_name,
        "creativePath": list(record.creative_path),
        "destination": str(destination),
        "evidence": dict(record.evidence),
        "ignoredMetadata": list(record.ignored_metadata),
        "language": record.language_code,
        "market": record.country_code,
        "marketKey": " ".join(item for item in [record.country_code, record.language_code] if item),
        "mediaType": record.asset_type,
        "platform": record.platform,
        "relativeDestination": destination.relative_to(root).as_posix(),
        "relativeSource": record.relative_source.as_posix(),
        "semanticPath": list(record.semantic_source_path),
        "source": str(record.source),
    }


def build_plan(
    root: Path,
    requested_order: Optional[List[Tuple[str, Optional[str]]]] = None,
) -> Tuple[List[AssetRecord], List[Dict[str, object]], List[AssetRecord], Dict[str, object]]:
    all_files = list(iter_launch_files(root))
    supported_files = [path for path in all_files if path.suffix.lower() in SUPPORTED_EXTENSIONS]
    records = [parse_record(root, path) for path in supported_files]
    candidates = [record for record in records if record.scope == "supported" and not record.reasons]
    unresolved = [record for record in records if record.scope == "unresolved"]
    out_of_scope = [record for record in records if record.scope == "out_of_scope"]

    base_map, display_map = build_market_labels(candidates, requested_order)
    asset_types_by_market = defaultdict(set)  # type: Dict[Tuple[str, Optional[str]], Set[str]]
    for record in candidates:
        asset_types_by_market[(record.country_code, record.language_code)].add(str(record.asset_type))
    for record in candidates:
        record.destination = destination_for_record(root, record, base_map, asset_types_by_market)

    destination_groups = defaultdict(list)  # type: Dict[str, List[AssetRecord]]
    for record in candidates:
        if record.destination:
            destination_groups[str(record.destination)].append(record)
    for group in destination_groups.values():
        platforms = {record.platform for record in group}
        if len(group) > 1 and len(platforms) == len(group) and None not in platforms:
            for record in group:
                record.destination = destination_for_record(
                    root, record, base_map, asset_types_by_market, include_platform=True
                )

    destination_groups = defaultdict(list)
    for record in candidates:
        if record.destination:
            destination_groups[str(record.destination)].append(record)
    conflicted = set()  # type: Set[int]
    for group in destination_groups.values():
        if len(group) > 1:
            for record in group:
                record.reasons.append("Destination collision could not be resolved safely")
                record.confidence = "low"
                record.scope = "unresolved"
                conflicted.add(id(record))

    for record in candidates:
        if id(record) in conflicted or record.destination is None or record.destination == record.source:
            continue
        if record.destination.exists():
            if files_are_identical(record.source, record.destination):
                record.reasons.append("Byte-identical duplicate preserved at both source and destination")
            else:
                record.reasons.append("Existing destination collision; no overwrite performed")
            record.confidence = "low"
            record.scope = "unresolved"
            conflicted.add(id(record))

    unresolved.extend(record for record in candidates if id(record) in conflicted)
    planned_records = [record for record in candidates if id(record) not in conflicted]
    moves = [move_preview(record, root) for record in planned_records]

    unsupported = [path for path in all_files if path.suffix.lower() not in SUPPORTED_EXTENSIONS]
    untouched = [record.relative_source.as_posix() for record in out_of_scope]
    untouched.extend(path.relative_to(root).as_posix() for path in unsupported)
    untouched.sort(key=natural_key)
    summary = {
        "clipboardOrderUsed": bool(requested_order),
        "marketCount": len(base_map),
        "markets": [re.sub(r"^\d+\s*-\s*", "", label) for label in display_map.values()],
        "otherFiles": 0,
        "resolvedFiles": len(planned_records),
        "systemJunk": [],
        "totalFiles": len(all_files),
        "unresolvedFiles": len(unresolved),
        "untouchedFiles": len(untouched),
        "untouched": untouched,
    }
    return records, moves, unresolved, summary


def print_summary(root: Path, summary: Dict[str, object], moves: List[Dict[str, object]], unresolved: List[AssetRecord]) -> None:
    print("\nCarpeta: " + str(root))
    print("Archivos detectados: " + str(summary["totalFiles"]))
    print("Archivos listos: " + str(summary["resolvedFiles"]))
    print("Archivos sin resolver: " + str(summary["unresolvedFiles"]))
    print("Archivos fuera de alcance, sin tocar: " + str(summary["untouchedFiles"]))
    print("Mercados detectados: " + (", ".join(summary["markets"]) if summary["markets"] else "ninguno"))
    if moves:
        print("\nPreview completo:")
        for move in moves:
            print("  " + str(move["action"]).upper() + ": " + str(move["relativeSource"]))
            print("    -> " + str(move["relativeDestination"]))
            print(
                "    market={market} language={language} platform={platform} media={mediaType} confidence={confidence}".format(
                    **move
                )
            )
            print("    semantic=" + "/".join(move["semanticPath"]) + " ignored=" + ", ".join(move["ignoredMetadata"]))
            print("    evidence=" + json.dumps(move["evidence"], ensure_ascii=False, sort_keys=True))
    if unresolved:
        print("\nSin resolver (no se mueven):")
        for record in unresolved:
            print("  " + record.relative_source.as_posix() + ": " + "; ".join(record.reasons))
            print("    evidence=" + json.dumps(record.evidence, ensure_ascii=False, sort_keys=True))
    if summary["untouched"]:
        print("\nFuera de alcance (sin tocar):")
        for relative in summary["untouched"]:
            print("  " + str(relative))


def unlock_for_move(path: Path, root: Path) -> None:
    paths = [path]
    current = path.parent
    while True:
        paths.append(current)
        if current == root:
            break
        current = current.parent
    try:
        for item in paths:
            item_stat = item.stat()
            flags = getattr(item_stat, "st_flags", 0)
            if flags & getattr(stat, "UF_IMMUTABLE", 0):
                os.chflags(item, flags & ~stat.UF_IMMUTABLE)
            if not item_stat.st_mode & stat.S_IWUSR:
                item.chmod(item_stat.st_mode | stat.S_IWUSR)
    except OSError as error:
        raise OrganizationError("No pude desbloquear '" + path.name + "'. Cerralo e intenta de nuevo.") from error


def files_are_identical(first: Path, second: Path) -> bool:
    try:
        if first.stat().st_size != second.stat().st_size:
            return False
        with first.open("rb") as first_file, second.open("rb") as second_file:
            while True:
                first_chunk = first_file.read(1024 * 1024)
                second_chunk = second_file.read(1024 * 1024)
                if first_chunk != second_chunk:
                    return False
                if not first_chunk:
                    return True
    except OSError:
        return False


def prune_source_ancestors(root: Path, relative_sources: List[str]) -> List[str]:
    removed = []  # type: List[str]
    candidates = set()  # type: Set[Path]
    for relative_source in relative_sources:
        current = (root / relative_source).parent
        while current != root:
            candidates.add(current)
            current = current.parent
    directories = sorted(
        candidates,
        key=lambda path: len(path.parts),
        reverse=True,
    )
    for path in directories:
        try:
            next(path.iterdir())
        except StopIteration:
            removed.append(path.relative_to(root).as_posix())
            path.rmdir()
    return removed


def missing_parent_directories(path: Path, root: Path) -> List[str]:
    missing = []  # type: List[str]
    current = path.parent
    while current != root and not current.exists():
        missing.append(current.relative_to(root).as_posix())
        current = current.parent
    return missing


def remove_created_directories(root: Path, relative_paths: List[str]) -> None:
    for relative in sorted(relative_paths, key=lambda value: len(Path(value).parts), reverse=True):
        path = root / relative
        try:
            path.rmdir()
        except OSError:
            pass


def restore_directories(root: Path, relative_paths: List[str]) -> None:
    for relative in sorted(relative_paths, key=lambda value: len(Path(value).parts)):
        (root / relative).mkdir(parents=True, exist_ok=True)


def rollback_moves(
    root: Path,
    applied_moves: List[Dict[str, str]],
    removed_directories: Optional[List[str]] = None,
    created_directories: Optional[List[str]] = None,
) -> None:
    for move in reversed(applied_moves):
        organized = root / move["to"]
        original = root / move["from"]
        if not organized.exists():
            continue
        if original.exists():
            raise OrganizationError("Rollback collision at " + move["from"])
        unlock_for_move(organized, root)
        original.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(organized), str(original))
    remove_created_directories(root, created_directories or [])
    restore_directories(root, removed_directories or [])


def write_json_atomic(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    os.replace(str(temporary), str(path))


def apply_plan(
    root: Path,
    moves: List[Dict[str, object]],
    unresolved: List[AssetRecord],
    system_junk: List[str],
) -> Path:
    del unresolved, system_junk
    executable = []  # type: List[Tuple[Path, Path, Dict[str, object]]]
    seen_destinations = set()  # type: Set[Path]
    for move in moves:
        source = root / str(move["relativeSource"])
        destination = root / str(move["relativeDestination"])
        if source == destination:
            continue
        if not source.exists():
            raise OrganizationError("No existe el archivo planeado: " + str(move["relativeSource"]))
        if destination.exists():
            raise OrganizationError("El destino ya existe; no se sobrescribio: " + str(move["relativeDestination"]))
        if destination in seen_destinations:
            raise OrganizationError("Dos archivos comparten destino: " + str(move["relativeDestination"]))
        seen_destinations.add(destination)
        executable.append((source, destination, move))

    metadata_dir = root / ".launch-organizer"
    undo_path = metadata_dir / "undo-last.json"
    if not executable:
        if not undo_path.exists():
            write_json_atomic(
                undo_path,
                {"createdAt": datetime.now().isoformat(timespec="seconds"), "root": str(root), "moves": [], "removedDirectories": []},
            )
        return undo_path

    applied = []  # type: List[Dict[str, str]]
    removed_directories = []  # type: List[str]
    created_directories = []  # type: List[str]
    metadata_dir_existed = metadata_dir.exists()
    try:
        for source, destination, move in executable:
            unlock_for_move(source, root)
            created_directories.extend(missing_parent_directories(destination, root))
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            applied.append(
                {"from": str(move["relativeSource"]), "to": str(move["relativeDestination"])}
            )
        removed_directories = prune_source_ancestors(
            root, [str(move["relativeSource"]) for move in moves if move["action"] == "move"]
        )
        write_json_atomic(
            undo_path,
            {
                "createdAt": datetime.now().isoformat(timespec="seconds"),
                "root": str(root),
                "moves": applied,
                "removedDirectories": removed_directories,
                "createdDirectories": sorted(set(created_directories), key=natural_key),
            },
        )
    except (OSError, OrganizationError) as error:
        try:
            rollback_moves(root, applied, removed_directories, created_directories)
        except (OSError, OrganizationError) as rollback_error:
            raise OrganizationError("Fallo la organizacion y tambien el rollback: " + str(rollback_error)) from error
        try:
            undo_path.with_name(undo_path.name + ".tmp").unlink()
        except OSError:
            pass
        if not metadata_dir_existed:
            try:
                metadata_dir.rmdir()
            except OSError:
                pass
        if isinstance(error, OrganizationError):
            raise
        raise OrganizationError("No pude completar la organizacion; restaure los movimientos aplicados.") from error
    return undo_path


def undo_last(root: Path) -> Optional[Path]:
    undo_path = root / ".launch-organizer" / "undo-last.json"
    if not undo_path.exists():
        return None
    try:
        payload = json.loads(undo_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise OrganizationError("El registro de undo no es legible.") from error
    moves = payload.get("moves", [])
    if not isinstance(moves, list):
        raise OrganizationError("El registro de undo no es valido.")

    pending = []  # type: List[Tuple[Path, Path, Dict[str, str]]]
    for move in reversed(moves):
        organized = root / move["to"]
        original = root / move["from"]
        if organized.exists() and not original.exists():
            pending.append((organized, original, move))
        elif original.exists() and not organized.exists():
            continue
        elif organized.exists() and original.exists():
            raise OrganizationError("Undo detenido para evitar sobrescribir: " + move["from"])
        else:
            raise OrganizationError("Undo detenido: faltan ambos lados de " + move["from"])

    reversed_moves = []  # type: List[Dict[str, str]]
    try:
        for organized, original, move in pending:
            unlock_for_move(organized, root)
            original.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(organized), str(original))
            reversed_moves.append(move)
        remove_created_directories(root, payload.get("createdDirectories", []))
        restore_directories(root, payload.get("removedDirectories", []))
    except (OSError, OrganizationError) as error:
        for move in reversed(reversed_moves):
            original = root / move["from"]
            organized = root / move["to"]
            organized.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(original), str(organized))
        raise OrganizationError("No pude completar el undo; restaure su estado anterior.") from error

    undo_path.unlink()
    try:
        undo_path.parent.rmdir()
    except OSError:
        pass
    return undo_path


def clean_dragged_path(raw_value: str) -> str:
    value = raw_value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return value.replace("\\ ", " ")


def build_summary_message(root: Path, summary: Dict[str, object], unresolved: List[AssetRecord]) -> str:
    lines = [
        "Carpeta: " + root.name,
        "Mercados detectados: " + (", ".join(summary["markets"]) if summary["markets"] else "ninguno"),
        "Archivos listos: " + str(summary["resolvedFiles"]),
        "Sin resolver: " + str(len(unresolved)),
        "Fuera de alcance, sin tocar: " + str(summary["untouchedFiles"]),
    ]
    return "\n".join(lines)


def ask_root_path() -> Path:
    while True:
        root = Path(clean_dragged_path(input("Arrastra la carpeta del lanzamiento aca y apreta Enter:\n> "))).expanduser()
        if root.exists() and root.is_dir():
            return root.resolve()
        print("No encontre esa carpeta. Probemos de nuevo.\n")


def interactive_mode() -> int:
    root = ask_root_path()
    action = input("\nElegi: [A]plicar, [P]review, [U]ndo (default A)\n> ").strip().lower() or "a"
    if action.startswith("u"):
        undone = undo_last(root)
        print("Undo aplicado." if undone else "No encontre un undo para esa carpeta.")
        return 0 if undone else 1
    _, moves, unresolved, summary = build_plan(root, clipboard_market_order())
    print_summary(root, summary, moves, unresolved)
    if action.startswith("p"):
        print("\nPreview listo. No movi nada.")
        return 0
    if input("\nAplicar este plan? [y/N]\n> ").strip().lower() != "y":
        return 0
    undo_path = apply_plan(root, moves, unresolved, summary["systemJunk"])
    print("\nListo. Undo guardado en: " + str(undo_path))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Ordena Meta y TikTok con preview y undo reversibles.")
    parser.add_argument("--root", help="Carpeta madre del lanzamiento")
    parser.add_argument("--preview", action="store_true", help="Muestra el plan sin escribir")
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
    if not root.is_dir():
        print("No existe la carpeta: " + str(root), file=sys.stderr)
        return 2
    if args.undo:
        undone = undo_last(root)
        if undone is None:
            print("No encontre un undo para esa carpeta.", file=sys.stderr)
            return 1
        print(str(undone))
        return 0
    _, moves, unresolved, summary = build_plan(root, clipboard_market_order())
    print_summary(root, summary, moves, unresolved)
    if args.preview or not args.apply:
        return 0
    undo_path = apply_plan(root, moves, unresolved, summary["systemJunk"])
    print("\nUndo guardado en: " + str(undo_path))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except OrganizationError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
