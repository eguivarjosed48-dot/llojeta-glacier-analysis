
from pathlib import Path
import re

import pandas as pd
import rasterio
from rasterio.errors import RasterioIOError


def parse_raster_name(filename: str) -> dict:
    stem = Path(filename).stem
    pattern = r'^(?P<epoch>\d{4}(?:_[A-Z])?)_(?P<product>DSM|Ortho)$'
    m = re.match(pattern, stem, flags=re.IGNORECASE)

    if not m:
        return {
            "filename": filename,
            "epoch": None,
            "product_type": None,
            "valid_name": False,
        }

    epoch = m.group("epoch")
    product = m.group("product").lower()

    return {
        "filename": filename,
        "epoch": epoch,
        "product_type": product,
        "valid_name": True,
    }


def inspect_raster(path: Path) -> dict:
    path = Path(path)

    info = {
        "path": str(path),
        "exists": path.exists(),
        "opened": False,
        "error": None,
        "crs": None,
        "width": None,
        "height": None,
        "count": None,
        "dtype": None,
        "nodata": None,
        "res_x": None,
        "res_y": None,
        "bounds_left": None,
        "bounds_bottom": None,
        "bounds_right": None,
        "bounds_top": None,
        "driver": None,
    }

    if not path.exists():
        info["error"] = "File does not exist"
        return info

    try:
        with rasterio.open(path) as src:
            info["opened"] = True
            info["crs"] = str(src.crs) if src.crs else None
            info["width"] = src.width
            info["height"] = src.height
            info["count"] = src.count
            info["dtype"] = src.dtypes[0] if src.count > 0 else None
            info["nodata"] = src.nodata
            info["res_x"] = src.res[0]
            info["res_y"] = src.res[1]
            info["bounds_left"] = src.bounds.left
            info["bounds_bottom"] = src.bounds.bottom
            info["bounds_right"] = src.bounds.right
            info["bounds_top"] = src.bounds.top
            info["driver"] = src.driver

    except RasterioIOError as e:
        info["error"] = f"RasterioIOError: {e}"
    except Exception as e:
        info["error"] = f"Unexpected error: {e}"

    return info


def build_raster_inventory(source_dir: Path) -> pd.DataFrame:
    source_dir = Path(source_dir)

    if not source_dir.exists():
        raise FileNotFoundError(f"No existe source_dir: {source_dir}")

    tif_files = sorted(source_dir.glob("*.tif"))
    records = []

    for tif in tif_files:
        parsed = parse_raster_name(tif.name)
        meta = inspect_raster(tif)

        record = {
            "filename": tif.name,
            "source_path": str(tif),
            "valid_name": parsed["valid_name"],
            "epoch": parsed["epoch"],
            "product_type": parsed["product_type"],
            **meta,
        }
        records.append(record)

    return pd.DataFrame(records)


def add_basic_qa(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["qa_exists"] = out["exists"] == True
    out["qa_opened"] = out["opened"] == True
    out["qa_has_crs"] = out["crs"].notna()
    out["qa_has_dimensions"] = (
        out["width"].fillna(0) > 0
    ) & (
        out["height"].fillna(0) > 0
    )
    out["qa_has_bands"] = out["count"].fillna(0) > 0
    out["qa_valid_name"] = out["valid_name"] == True

    out["qa_ok"] = (
        out["qa_exists"] &
        out["qa_opened"] &
        out["qa_has_crs"] &
        out["qa_has_dimensions"] &
        out["qa_has_bands"] &
        out["qa_valid_name"]
    )

    return out


def summarize_pairs(df: pd.DataFrame, expected_epochs=None) -> pd.DataFrame:
    if expected_epochs is None:
        expected_epochs = sorted(set(df["epoch"].dropna().tolist()))

    expected_products = {"dsm", "ortho"}
    pair_records = []

    for epoch in expected_epochs:
        epoch_rows = df[df["epoch"] == epoch]
        present_products = set(epoch_rows["product_type"].dropna().str.lower().tolist())

        pair_records.append({
            "epoch": epoch,
            "has_dsm": "dsm" in present_products,
            "has_ortho": "ortho" in present_products,
            "pair_complete": expected_products.issubset(present_products),
        })

    return pd.DataFrame(pair_records)
