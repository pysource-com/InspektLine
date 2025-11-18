import os
import random
import shutil
from typing import List, Tuple


class DatasetSplitter:
    """
    Split a dataset organized as:

        src_root/
            class1/
                img1.jpg
                ...
            class2/
                ...
            ...

    into:

        dst_root/
            train/
                class1/...
                class2/...
            val/
                class1/...
                class2/...
            test/
                class1/...
                class2/...

    test_size and val_size are fractions in [0, 1].
    train_size is computed as 1 - test_size - val_size.
    """

    def __init__(
        self,
        src_root: str,
        dst_root: str,
        test_size: float = 0.1,
        val_size: float = 0.1,
        seed: int = 42,
        exts: Tuple[str, ...] = (".jpg", ".jpeg", ".png", ".bmp", ".gif"),
    ) -> None:
        self.src_root = src_root
        self.dst_root = dst_root
        self.test_size = test_size
        self.val_size = val_size
        self.seed = seed
        self.exts = tuple(e.lower() for e in exts)

        if test_size < 0 or val_size < 0 or test_size + val_size >= 1.0:
            raise ValueError("test_size and val_size must be >= 0 and sum to < 1.0")

        random.seed(self.seed)

    def split(self) -> None:
        """Perform the split for all class subfolders."""
        class_names = self._list_classes()
        for cls in class_names:
            self._split_class(cls)

    def _list_classes(self) -> List[str]:
        """Return list of class folder names inside src_root."""
        return [
            d
            for d in os.listdir(self.src_root)
            if os.path.isdir(os.path.join(self.src_root, d))
        ]

    def _list_images(self, class_name: str) -> List[str]:
        """Return full paths of image files for a given class."""
        class_dir = os.path.join(self.src_root, class_name)
        files = []
        for fname in os.listdir(class_dir):
            path = os.path.join(class_dir, fname)
            if os.path.isfile(path) and fname.lower().endswith(self.exts):
                files.append(path)
        return files

    def _split_indices(self, n: int) -> Tuple[List[int], List[int], List[int]]:
        """Return indices for train, val, test splits."""
        indices = list(range(n))
        random.shuffle(indices)

        n_test = int(round(n * self.test_size))
        n_val = int(round(n * self.val_size))

        test_idx = indices[:n_test]
        val_idx = indices[n_test : n_test + n_val]
        train_idx = indices[n_test + n_val :]

        return train_idx, val_idx, test_idx

    def _ensure_dir(self, *parts: str) -> str:
        path = os.path.join(*parts)
        os.makedirs(path, exist_ok=True)
        return path

    def _copy_files(
        self,
        files: List[str],
        indices: List[int],
        split_name: str,
        class_name: str,
    ) -> None:
        dst_dir = self._ensure_dir(self.dst_root, split_name, class_name)
        for idx in indices:
            src_path = files[idx]
            fname = os.path.basename(src_path)
            dst_path = os.path.join(dst_dir, fname)
            shutil.copy2(src_path, dst_path)
            # if you prefer move instead of copy, use:
            # shutil.move(src_path, dst_path)

    def _split_class(self, class_name: str) -> None:
        files = self._list_images(class_name)
        if not files:
            return

        train_idx, val_idx, test_idx = self._split_indices(len(files))

        self._copy_files(files, train_idx, "train", class_name)
        self._copy_files(files, val_idx, "val", class_name)
        self._copy_files(files, test_idx, "test", class_name)

# Example usage:
if __name__ == "__main__":
    splitter = DatasetSplitter(
        src_root=r"D:\Dataset\Classification\car_colors\Colors",
        dst_root="../samples/splitted_dataset",
        test_size=0.1,
        val_size=0.1,
        seed=123,
    )
    splitter.split()