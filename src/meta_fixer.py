import os
from collections import defaultdict
from pathlib import Path

from chardet import detect
from mutagen.easyid3 import EasyID3


class MetaFixer:
    def __init__(self, folder_path: Path = None) -> None:
        if folder_path is None:
            self.folder_path = Path(".") / "files"
        else:
            self.folder_path = folder_path
        self.files = None
        self.metadata_original = None
        self.metadata_fixed = None

    @staticmethod
    def _fix_encoding(text: str) -> str:
        try:
            # Step 1: Get raw bytes by encoding with Latin-1 (1:1 byte map)
            raw_bytes = text.encode("latin1")
        except UnicodeEncodeError:
            return None

        # Try encoding detection with chardet
        detected = detect(raw_bytes)
        enc = detected["encoding"]
        confidence = detected["confidence"]

        # If chardet is confident enough, try decoding with it
        if enc and confidence > 0.7:
            try:
                return raw_bytes.decode(enc)
            except UnicodeDecodeError:
                pass

        # TODO: Get encoding with maximum confidence?
        # Fallback: Try a list of known East Asian encodings
        for candidate in [
            "cp949",
            "euc-kr",
            "shift_jis",
            "euc_jp",
            "iso2022_jp",
        ]:
            try:
                return raw_bytes.decode(candidate)
            except UnicodeDecodeError:
                continue

        return None

    def get_files(self) -> bool:
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

    def _extract_metadata(self, file_path: Path) -> dict:
        audio = EasyID3(file_path)
        keys = ("album", "title", "artist", "genre")

        meta = {}
        for key in keys:
            if key in audio:
                meta[key] = audio[key][0]
            else:
                meta[key] = None

        return meta

    def get_original_metadata(self) -> bool:
        meta = defaultdict(dict)
        for folder, files in self.files.items():
            for file in files:
                f_meta = self._extract_metadata(file)
                meta[file] = f_meta

        self.metadata_original = dict(meta)

        return len(meta) > 0

    def run(self):
        # Get files and their original metadata
        if self.get_files():
            self.get_original_metadata()

        print(self._fix_encoding("üåª¨ªÊª¤íþª¤ìíèøìí"))


if __name__ == "__main__":
    fixer = MetaFixer()
    fixer.run()
    pass
