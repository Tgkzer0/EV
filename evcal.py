import argparse
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional

import pandas as pd

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, simpledialog
except Exception:
    tk = None
    filedialog = None
    messagebox = None
    simpledialog = None


RARITY_ORDER = [
    "common",
    "uncommon",
    "rare",
    "super rare",
    "secret rare",
    "alternate art",
]

RARITY_ALIASES = {
    "c": "common",
    "common": "common",
    "u": "uncommon",
    "uc": "uncommon",
    "uncommon": "uncommon",
    "r": "rare",
    "rare": "rare",
    "rr": "rare",
    "sr": "super rare",
    "super": "super rare",
    "super rare": "super rare",
    "sec": "secret rare",
    "scr": "secret rare",
    "secret": "secret rare",
    "secret rare": "secret rare",
    "aa": "alternate art",
    "alt": "alternate art",
    "alt art": "alternate art",
    "alternate": "alternate art",
    "alternate art": "alternate art",
}

ALT_ART_PATTERNS = [
    r"\balternate art\b",
    r"\balt art\b",
    r"\balt\.?\b",
    r"\bparallel\b",
]

PRICE_COLUMNS = [
    "TCG Market Price",
    "Market Price",
    "Listed Median Price",
    "Median Price",
    "Low Price",
    "Price",
]

NAME_COLUMNS = ["Product Name", "Name", "Card Name", "Title"]
RARITY_COLUMNS = ["Rarity", "Card Rarity", "Variant"]


@dataclass
class PullProfile:
    name: str
    packs_per_box: int
    boxes_per_case: int
    commons_per_pack: int
    uncommons_per_pack: int
    super_rares_per_box: int
    secret_rares_per_case: int
    alternate_arts_per_case: int

    @property
    def total_packs(self) -> int:
        return self.packs_per_box * self.boxes_per_case


DEFAULT_PROFILES = {
    "normal": PullProfile("Normal", 24, 12, 7, 3, 7, 6, 24),
    "bt": PullProfile("BT", 24, 12, 7, 3, 7, 8, 16),
    "ex": PullProfile("EX", 24, 12, 7, 3, 7, 69, 420),
}


def first_existing_column(columns: Iterable[str], candidates: Iterable[str]) -> Optional[str]:
    lookup = {column.strip().lower(): column for column in columns}
    for candidate in candidates:
        match = lookup.get(candidate.lower())
        if match:
            return match
    return None


def clean_price(value) -> float:
    if pd.isna(value):
        return 0.0
    cleaned = re.sub(r"[^0-9.\-]", "", str(value))
    if cleaned in {"", ".", "-", "-."}:
        return 0.0
    try:
        return max(float(cleaned), 0.0)
    except ValueError:
        return 0.0


def normalize_rarity(value) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip().lower())
    return RARITY_ALIASES.get(text, text)


def looks_like_alt_art(name: str) -> bool:
    text = str(name or "").lower()
    return any(re.search(pattern, text) for pattern in ALT_ART_PATTERNS)


def google_drive_file_id(source: str) -> Optional[str]:
    patterns = [
        r"/d/([\w-]+)",
        r"[?&]id=([\w-]+)",
        r"/open\?id=([\w-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, source)
        if match:
            return match.group(1)
    return None


def resolve_csv_source(source: str) -> str:
    source = source.strip().strip('"')
    if not source:
        raise ValueError("No CSV file or link was provided.")

    if "drive.google.com" not in source:
        return source

    file_id = google_drive_file_id(source)
    if not file_id:
        raise ValueError("That Google Drive link does not look like a share link.")

    try:
        import gdown
    except ImportError as exc:
        raise ValueError("Google Drive links require gdown. Run: pip install -r requirements.txt") from exc

    output_path = os.path.join(tempfile.gettempdir(), f"ev_prices_{file_id}.csv")
    downloaded = gdown.download(
        f"https://drive.google.com/uc?id={file_id}",
        output_path,
        quiet=False,
        fuzzy=True,
    )
    if not downloaded:
        raise ValueError("The Google Drive CSV could not be downloaded.")
    return output_path


def load_card_data(source: str) -> pd.DataFrame:
    csv_path = resolve_csv_source(source)
    df = pd.read_csv(csv_path)

    price_col = first_existing_column(df.columns, PRICE_COLUMNS)
    rarity_col = first_existing_column(df.columns, RARITY_COLUMNS)
    name_col = first_existing_column(df.columns, NAME_COLUMNS)

    if not price_col:
        raise ValueError(f"No price column found. Expected one of: {', '.join(PRICE_COLUMNS)}")
    if not rarity_col:
        raise ValueError(f"No rarity column found. Expected one of: {', '.join(RARITY_COLUMNS)}")

    df["ev_price"] = df[price_col].apply(clean_price)
    df["ev_rarity"] = df[rarity_col].apply(normalize_rarity)

    if name_col:
        alt_mask = df[name_col].apply(looks_like_alt_art)
        df.loc[alt_mask, "ev_rarity"] = "alternate art"

    return df[df["ev_price"] > 0].copy()


def prompt_text(root, title: str, prompt: str, default: str = "") -> str:
    value = simpledialog.askstring(title, prompt, initialvalue=default, parent=root)
    return "" if value is None else value.strip()


def prompt_float(root, title: str, prompt: str, default: float) -> float:
    value = simpledialog.askfloat(title, prompt, initialvalue=default, minvalue=0, parent=root)
    if value is None:
        raise KeyboardInterrupt
    return float(value)


def prompt_int(root, title: str, prompt: str, default: int) -> int:
    value = simpledialog.askinteger(title, prompt, initialvalue=default, minvalue=0, parent=root)
    if value is None:
        raise KeyboardInterrupt
    return int(value)


def choose_csv_source(root) -> str:
    source = prompt_text(
        root,
        "Card price CSV",
        "Paste a local CSV path, Google Drive share link, or direct CSV URL.\n\nLeave blank to browse for a file.",
    )
    if source:
        return source

    path = filedialog.askopenfilename(
        parent=root,
        title="Choose a card price CSV",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
    )
    if not path:
        raise KeyboardInterrupt
    return path


def profile_from_gui(root) -> PullProfile:
    choice = prompt_text(root, "Product type", "Choose a profile: Normal, BT, or EX", "Normal").lower()
    profile = DEFAULT_PROFILES.get(choice, DEFAULT_PROFILES["normal"])

    if messagebox.askyesno("Pull rates", "Do you want to change pack, box, or pull-rate defaults?", parent=root):
        return PullProfile(
            profile.name,
            prompt_int(root, "Pull rates", "Packs per box", profile.packs_per_box),
            prompt_int(root, "Pull rates", "Boxes per case", profile.boxes_per_case),
            prompt_int(root, "Pull rates", "Commons per pack", profile.commons_per_pack),
            prompt_int(root, "Pull rates", "Uncommons per pack", profile.uncommons_per_pack),
            prompt_int(root, "Pull rates", "Super rares per box", profile.super_rares_per_box),
            prompt_int(root, "Pull rates", "Secret rares per case", profile.secret_rares_per_case),
            prompt_int(root, "Pull rates", "Alternate arts per case", profile.alternate_arts_per_case),
        )
    return profile


def profile_from_args(args) -> PullProfile:
    base = DEFAULT_PROFILES[args.profile.lower()]
    return PullProfile(
        base.name,
        args.packs_per_box if args.packs_per_box is not None else base.packs_per_box,
        args.boxes_per_case if args.boxes_per_case is not None else base.boxes_per_case,
        args.commons_per_pack if args.commons_per_pack is not None else base.commons_per_pack,
        args.uncommons_per_pack if args.uncommons_per_pack is not None else base.uncommons_per_pack,
        args.super_rares_per_box if args.super_rares_per_box is not None else base.super_rares_per_box,
        args.secret_rares_per_case if args.secret_rares_per_case is not None else base.secret_rares_per_case,
        args.alternate_arts_per_case
        if args.alternate_arts_per_case is not None
        else base.alternate_arts_per_case,
    )


def build_pull_counts(profile: PullProfile) -> Dict[str, int]:
    total_packs = profile.total_packs
    super_rares = profile.super_rares_per_box * profile.boxes_per_case
    secret_rares = profile.secret_rares_per_case
    alternate_arts = profile.alternate_arts_per_case
    rares = max(total_packs - super_rares - secret_rares - alternate_arts, 0)

    return {
        "common": profile.commons_per_pack * total_packs,
        "uncommon": profile.uncommons_per_pack * total_packs,
        "rare": rares,
        "super rare": super_rares,
        "secret rare": secret_rares,
        "alternate art": alternate_arts,
    }


def calculate_ev(
    df: pd.DataFrame,
    profile: PullProfile,
    fee_percent: float,
    price_adjustment_percent: float,
    case_cost: float,
) -> Dict[str, object]:
    pull_counts = build_pull_counts(profile)
    fee_multiplier = max(1 - fee_percent / 100, 0)
    price_multiplier = max(price_adjustment_percent / 100, 0)

    rows = []
    gross_case_ev = 0.0
    net_case_ev = 0.0

    for rarity in RARITY_ORDER:
        prices = df.loc[df["ev_rarity"] == rarity, "ev_price"]
        pull_count = pull_counts.get(rarity, 0)
        average_price = float(prices.mean()) if not prices.empty else 0.0
        gross_value = average_price * pull_count
        net_value = gross_value * price_multiplier * fee_multiplier
        gross_case_ev += gross_value
        net_case_ev += net_value
        rows.append(
            {
                "rarity": rarity,
                "cards_found": int(prices.count()),
                "pulls_per_case": pull_count,
                "avg_market_price": average_price,
                "gross_case_ev": gross_value,
                "net_case_ev": net_value,
            }
        )

    box_ev = net_case_ev / profile.boxes_per_case if profile.boxes_per_case else 0.0
    pack_ev = net_case_ev / profile.total_packs if profile.total_packs else 0.0
    profit = net_case_ev - case_cost
    roi = (profit / case_cost * 100) if case_cost else 0.0

    return {
        "profile": profile,
        "rows": rows,
        "gross_case_ev": gross_case_ev,
        "net_case_ev": net_case_ev,
        "box_ev": box_ev,
        "pack_ev": pack_ev,
        "case_cost": case_cost,
        "profit": profit,
        "roi": roi,
        "break_even_case": net_case_ev,
        "break_even_box": box_ev,
        "break_even_pack": pack_ev,
    }


def format_money(value: float) -> str:
    return f"${value:,.2f}"


def format_summary(result: Dict[str, object]) -> str:
    profile = result["profile"]
    verdict = "Worth considering" if result["profit"] >= 0 else "Skip at this price"
    lines = [
        f"Verdict: {verdict}",
        "",
        f"Profile: {profile.name}",
        f"Packs per box: {profile.packs_per_box}",
        f"Boxes per case: {profile.boxes_per_case}",
        "",
        f"Gross market EV per case: {format_money(result['gross_case_ev'])}",
        f"Net resale EV per case: {format_money(result['net_case_ev'])}",
        f"Net resale EV per box: {format_money(result['box_ev'])}",
        f"Net resale EV per pack: {format_money(result['pack_ev'])}",
        "",
        f"Your case cost: {format_money(result['case_cost'])}",
        f"Expected profit/loss per case: {format_money(result['profit'])}",
        f"Expected ROI: {result['roi']:.1f}%",
        "",
        "Break-even max buy prices:",
        f"Case: {format_money(result['break_even_case'])}",
        f"Box: {format_money(result['break_even_box'])}",
        f"Pack: {format_money(result['break_even_pack'])}",
        "",
        "Rarity breakdown:",
    ]

    for row in result["rows"]:
        lines.append(
            f"- {row['rarity'].title()}: {row['pulls_per_case']} pulls, "
            f"{row['cards_found']} cards found, avg {format_money(row['avg_market_price'])}, "
            f"net EV {format_money(row['net_case_ev'])}"
        )

    return "\n".join(lines)


def save_breakdown(result: Dict[str, object], output_path: str) -> None:
    pd.DataFrame(result["rows"]).to_csv(output_path, index=False)


def run_gui() -> int:
    if tk is None:
        print("Tkinter is not available. Use command line mode instead.", file=sys.stderr)
        return 1

    root = tk.Tk()
    root.withdraw()
    try:
        source = choose_csv_source(root)
        profile = profile_from_gui(root)
        case_cost = prompt_float(root, "Purchase cost", "What is your total buy cost for one case?", 0.0)
        fee_percent = prompt_float(root, "Selling fees", "Marketplace/payment fee percent", 13.0)
        price_adjustment = prompt_float(
            root,
            "Realistic sale price",
            "Percent of market price you expect to actually receive",
            90.0,
        )

        df = load_card_data(source)
        result = calculate_ev(df, profile, fee_percent, price_adjustment, case_cost)
        summary = format_summary(result)
        messagebox.showinfo("EV resale calculator", summary, parent=root)

        if messagebox.askyesno("Save breakdown", "Save the rarity breakdown as a CSV?", parent=root):
            save_path = filedialog.asksaveasfilename(
                parent=root,
                title="Save EV breakdown",
                defaultextension=".csv",
                initialfile="ev_breakdown.csv",
                filetypes=[("CSV files", "*.csv")],
            )
            if save_path:
                save_breakdown(result, save_path)
                messagebox.showinfo("Saved", f"Breakdown saved to:\n{save_path}", parent=root)
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        messagebox.showerror("EV calculator error", str(exc), parent=root)
        return 1
    finally:
        root.destroy()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Calculate sealed product resale EV from a card price CSV.")
    parser.add_argument("--csv", help="Local CSV path, direct CSV URL, or Google Drive share link.")
    parser.add_argument("--profile", choices=sorted(DEFAULT_PROFILES), default="normal")
    parser.add_argument("--case-cost", type=float, default=0.0, help="Total buy cost for one case.")
    parser.add_argument("--fee-percent", type=float, default=13.0, help="Marketplace/payment fee percent.")
    parser.add_argument(
        "--price-adjustment-percent",
        type=float,
        default=90.0,
        help="Percent of listed market price you expect to actually receive.",
    )
    parser.add_argument("--packs-per-box", type=int)
    parser.add_argument("--boxes-per-case", type=int)
    parser.add_argument("--commons-per-pack", type=int)
    parser.add_argument("--uncommons-per-pack", type=int)
    parser.add_argument("--super-rares-per-box", type=int)
    parser.add_argument("--secret-rares-per-case", type=int)
    parser.add_argument("--alternate-arts-per-case", type=int)
    parser.add_argument("--output", help="Optional CSV path for the rarity breakdown.")
    return parser


def run_cli(args) -> int:
    if not args.csv:
        return run_gui()

    profile = profile_from_args(args)
    df = load_card_data(args.csv)
    result = calculate_ev(df, profile, args.fee_percent, args.price_adjustment_percent, args.case_cost)
    print(format_summary(result))

    if args.output:
        save_breakdown(result, args.output)
        print(f"\nSaved breakdown to {Path(args.output).resolve()}")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return run_cli(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
