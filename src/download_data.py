import argparse
import hashlib
import shutil
import tempfile
import zipfile
from pathlib import Path

import kagglehub

from src.config import RAW_CSV, ensure_directories


DATASET_HANDLE = "shashwatwork/dataco-smart-supply-chain-for-big-data-analysis/versions/1"
SOURCE_FILENAME = "DataCoSupplyChainDataset.csv"
EXPECTED_SHA256 = "fa6d022ed437155e1a2f0378710602848703c8a7f203f7ff5d77805bf8480aa6"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_data(force: bool = False) -> Path:
    ensure_directories()
    if RAW_CSV.exists() and not force:
        current_hash = _sha256(RAW_CSV)
        if current_hash == EXPECTED_SHA256:
            print(f"Official Kaggle file already present: {RAW_CSV}")
            return RAW_CSV
        raise FileExistsError(
            f"{RAW_CSV} already exists with SHA-256 {current_hash}. "
            "Use --force to replace it with the Kaggle version."
        )

    with tempfile.TemporaryDirectory(prefix="dataco_kaggle_") as temporary_directory:
        downloaded = Path(
            kagglehub.dataset_download(
                DATASET_HANDLE,
                path=SOURCE_FILENAME,
                output_dir=temporary_directory,
                force_download=True,
            )
        )
        source = downloaded
        if zipfile.is_zipfile(downloaded):
            extract_directory = Path(temporary_directory) / "extracted"
            with zipfile.ZipFile(downloaded) as archive:
                archive.extract(SOURCE_FILENAME, extract_directory)
            source = extract_directory / SOURCE_FILENAME

        observed_hash = _sha256(source)
        if observed_hash != EXPECTED_SHA256:
            raise ValueError(
                f"Kaggle file hash changed: expected {EXPECTED_SHA256}, "
                f"observed {observed_hash}. Review the dataset version before continuing."
            )
        shutil.copyfile(source, RAW_CSV)

    print(f"Downloaded and verified official Kaggle data: {RAW_CSV}")
    return RAW_CSV


def main() -> None:
    parser = argparse.ArgumentParser(description="Download the official DataCo Kaggle CSV.")
    parser.add_argument(
        "--force", action="store_true", help="Replace an existing raw CSV after validation."
    )
    arguments = parser.parse_args()
    download_data(force=arguments.force)


if __name__ == "__main__":
    main()
