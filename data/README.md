# Data directory

Download `DataCoSupplyChainDataset.csv` directly from Kaggle with:

```powershell
python -m src.download_data
```

The command uses Kaggle's official `kagglehub` client and places the extracted CSV here:

```text
data/raw/DataCoSupplyChainDataset.csv
```

The pipeline reads the file with Latin-1 encoding. Raw data, generated SQLite databases, and analytical exports are ignored by Git.

Expected source contract:

- 180,519 rows
- 53 columns
- File name: `DataCoSupplyChainDataset.csv`
- Order-item grain

Authoritative source: <https://doi.org/10.17632/8gx2fvg2k6.5>

Kaggle distribution: <https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis>

The validated version-1 Kaggle file has this byte-level SHA-256 hash:

```text
fa6d022ed437155e1a2f0378710602848703c8a7f203f7ff5d77805bf8480aa6
```

Some public mirrors normalize CRLF line endings to LF. Their normalized content can be identical while their byte-level checksum differs.

