from pathlib import Path


MODEL_FILES = ("movies.pkl", "similrity.pkl")
LFS_POINTER_PREFIX = b"version https://git-lfs.github.com/spec"


def main():
    for filename in MODEL_FILES:
        path = Path(filename)

        if not path.exists():
            raise SystemExit(f"{filename} is missing")

        first_bytes = path.read_bytes()[:64]

        if first_bytes.startswith(LFS_POINTER_PREFIX):
            raise SystemExit(
                f"{filename} is a Git LFS pointer file. "
                "Run git lfs pull before building or starting the app."
            )

        print(f"{filename} is available")


if __name__ == "__main__":
    main()
