"""Download the pinned IBM Telco Customer Churn sample dataset."""

from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen


DATASET_COMMIT = "d5371f5d83a446ad5673cbcca3b814b926491f8a"
DATASET_URL = (
    "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/"
    + DATASET_COMMIT
    + "/data/Telco-Customer-Churn.csv"
)
DATASET_SHA256 = "16320c9c1ec72448db59aa0a26a0b95401046bef5d02fd3aeb906448e3055e91"
DATA_PATH = Path(__file__).resolve().parents[1] / "data/raw/Telco-Customer-Churn.csv"


def download_dataset(destination: Path = DATA_PATH) -> Path:
    """Download the exact source version and verify its SHA-256 checksum."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(DATASET_URL, headers={"User-Agent": "customer-churn-analysis/1.0"})
    with urlopen(request, timeout=60) as response:
        content = response.read()
    checksum = sha256(content).hexdigest()
    if checksum != DATASET_SHA256:
        raise ValueError("Downloaded dataset checksum does not match the pinned IBM source.")
    destination.write_bytes(content)
    return destination


if __name__ == "__main__":
    print(download_dataset())
