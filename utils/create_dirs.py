from pathlib import Path


extension_mapping = {
                'image/jpg': 'jpg',
                'image/jpeg': 'jpg',
                'image/png': 'png',
                'image/webp': 'webp'
                }


def create_directory(path: Path) -> Path:
    """Create directory if it doesn't exist"""
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def check_valid_output(path):
    if path == None:
        path = Path(__file__).parent / "download"
    else:
        path = Path(path)

    if not path.exists():
        path.mkdir(parents=True)

    return path