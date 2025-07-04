import os
from collections import defaultdict
from pathlib import Path

from mutagen.id3 import ID3


class MetaFixer:
    def __init__(self, folder_path: Path = None) -> None:
        if folder_path is None:
            self.folder_path = Path(".") / "files"
        else:
            self.folder_path = folder_path
        self.files = None

    def _get_files(self) -> bool:
        """Method to walk through the parent folder and retrieve all audio
        files.

        Returns:
            bool: True if more than one file has been found.
        """

        # Walk through the root folder and retrieve all audio files
        all_files = [
            (dirs[0], file)
            for dirs in os.walk(self.folder_path)
            for file in dirs[2]
        ]

        # Merge files per each subdirectory
        files = defaultdict(list)
        for folder, file in all_files:
            file_path = self.folder_path / os.path.split(folder)[1] / file
            files[folder].append(file_path)
        self.files = dict(files)

        return len(files) > 0

    def _extract_metadata(self, file_path: Path):
        audio = ID3(file_path)
        for tag in audio.values():
            try:
                print(tag.FrameID, tag.text)
            except AttributeError:
                continue

    def run(self):
        self._get_files()
        for folder, files in self.files.items():
            for file in files:
                self._extract_metadata(file.key)


if __name__ == "__main__":
    fixer = MetaFixer()
    fixer.run()
    pass
