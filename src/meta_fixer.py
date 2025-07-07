import os
from collections import defaultdict
from csv import DictWriter
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
    def _is_garbled(text: str) -> bool:
        """Helper static method to detect if a string is garbled or not.

        Args:
            text (str): Input string to run detection for.

        Returns:
            bool: True if the text is garbled, False if not.
        """

        # If it contains printable ASCII or odd punctuation but few CJK chars
        return any(
            "\u3040" <= c <= "\u30ff"  # Japanese
            or "\u4e00" <= c <= "\u9fff"  # CJK Unified Ideographs
            or "\uac00" <= c <= "\ud7a3"  # Korean Hangul
            for c in text
        )

    @staticmethod
    def _fix_encoding(text: str) -> str:
        """Helper static method to fix character encoding issues of a string.

        Args:
            text (str): Input string to fix encoding issues for.

        Returns:
            str: Fixed version of the string.
        """

        if not text:
            return None

        try:
            # If the string looks good, return it as is
            if not MetaFixer._is_garbled(text):
                return text
            # Get raw bytes assuming text is incorrectly decoded from latin1
            raw_bytes = text.encode("latin1")
        except UnicodeEncodeError:
            # If not Latin1-compatible, assume it's fine
            return text

        # Try encoding detection with chardet
        detected = detect(raw_bytes)
        enc = detected["encoding"]
        confidence = detected["confidence"]

        # If chardet is confident enough, try decoding with it
        if enc and confidence > 0.8:
            try:
                return raw_bytes.decode(enc)
            except UnicodeDecodeError:
                pass

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
        """Helper method to extract the key audio metadata for a single file.

        Args:
            file_path (Path): Path of the audio file.

        Returns:
            dict: Extracted metadata of the audio file.
        """

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
        """Method to extract the metadata of all files.

        Returns:
            bool: True if metadata is extracted for more than 1 file.
        """

        print("Extracting metadata...")

        meta = defaultdict(dict)
        for folder, files in self.files.items():
            for file in files:
                f_meta = self._extract_metadata(file)
                meta[file] = f_meta

        self.metadata_original = dict(meta)

        return len(meta) > 0

    def fix_extracted_metadata(self) -> bool:
        """Method to fix the extracted metadata of audio files.

        Returns:
            bool: True after completion.
        """

        print("Fixing metadata...")

        fixed_meta = defaultdict(dict)
        for file, metadata in self.metadata_original.items():
            # Open the audio file
            audio = EasyID3(file)
            fixed = {}
            for tag, value in metadata.items():
                # Fix encoding of the tag
                fixed_val = self._fix_encoding(value)
                # Save the fixed tag value
                fixed[tag] = fixed_val
                # Update the file's metadata tag
                audio[tag] = fixed_val
            # Save the fixed metadata results
            fixed_meta[file] = fixed
            audio.save()

        self.metadata_fixed = dict(fixed_meta)

        return True

    def output_results(self) -> bool:
        """Method to output the results of the fixing in a simple CSV file.

        Returns:
            bool: True after completion.
        """

        field_names = (
            "file_path",
            "artist_og",
            "artist_fixed",
            "title_og",
            "title_fixed",
            "album_og",
            "album_fixed",
            "genre_og",
            "genre_fixed",
        )

        # Write the results of the metadata fixing to a CSV file
        with open("results.csv", "w", newline="") as f:
            writer = DictWriter(f, fieldnames=field_names)
            writer.writeheader()

            for f_path, meta_og in self.metadata_original.items():
                row = {}
                # Extract original metadata to write into row
                for tag, value in meta_og.items():
                    og_tag = f"{tag}_og"
                    row[og_tag] = value
                # Extract fixed metadata to write into row
                for tag, value in self.metadata_fixed[f_path].items():
                    fixed_tag = f"{tag}_fixed"
                    row[fixed_tag] = value
                # Save filepath for row
                row["file_path"] = f_path
                # Write row into result file
                writer.writerow(row)

        return True

    def run(self):
        # Get files and their original metadata
        if self.get_files():
            self.get_original_metadata()
        # Fix metadata of the retrieved files
        self.fix_extracted_metadata()
        # Give output CSV of results
        self.output_results()


if __name__ == "__main__":
    fixer = MetaFixer()
    fixer.run()
