import os
from csv import DictWriter
from pathlib import Path

from chardet import detect
from mutagen import id3
from mutagen.easyid3 import EasyID3
from tqdm import tqdm


class MetaFixer:
    def __init__(self, folder_path: Path = None) -> None:
        if folder_path is None:
            self.folder_path = Path(".") / "files"
        else:
            self.folder_path = folder_path
        self.file_paths = None
        self.metadata = None

        # Keys of metadata to extract
        self.keys = ("album", "title", "artist", "genre")

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

    def _get_files(self) -> bool:
        """Method to walk through the parent folder and retrieve all audio
        files.

        Returns:
            bool: True if more than one file has been found.
        """

        # Get full path of all files in the file folder
        all_files = [
            self.folder_path / f for f in os.listdir(self.folder_path)
        ]
        # Create and save dictionary of metadata
        metadata = {
            f_path: {"original": None, "fixed": None} for f_path in all_files
        }
        # Save as instance variables
        self.file_paths = all_files
        self.metadata = metadata

        return len(all_files) > 0

    def _extract_metadata(self, f_path: Path, audio: EasyID3) -> dict:
        # Extract original metadata
        meta = {}
        for key in self.keys:
            if key in audio:
                meta[key] = audio[key][0]
            else:
                meta[key] = None
        # Save extracted metadata
        self.metadata[f_path]["original"] = meta

        return meta

    def _fix_metadata(self, f_path: Path, meta: dict, audio: EasyID3) -> bool:
        is_fixed = False
        fixed_meta = {}
        for tag, value in meta.items():
            # Fix encoding of the tag
            fixed_val = self._fix_encoding(value)
            # If the fix attempt was successful
            if fixed_val:
                # Save the fixed tag value
                fixed_meta[tag] = fixed_val
                # If a corrupted metadata was fixed
                if fixed_val != value:
                    # Update the file's metadata tag
                    audio[tag] = fixed_val
                    # Update the boolean tracker
                    is_fixed = True
        # Save the fixed metadata results
        self.metadata[f_path]["fixed"] = fixed_meta
        # Save the audio file with fixed metadta
        audio.save()

        return is_fixed

    def _fix_files(self) -> int:
        fixed_count = 0
        for f_path in tqdm(self.file_paths):
            try:
                # Try opening the file in mutagen
                audio = EasyID3(f_path)
                # Extract the original metdata
                meta = self._extract_metadata(f_path, audio)
                # Fix extracted metadata
                fixed = self._fix_metadata(f_path, meta, audio)
                if fixed:
                    fixed_count += 1
            except id3._util.ID3NoHeaderError:
                pass

        return fixed_count

    def _output_results(self) -> bool:
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
        with open("results.csv", "w", encoding="utf-8", newline="") as f:
            writer = DictWriter(f, fieldnames=field_names)
            writer.writeheader()

            for f_path, meta_dict in self.metadata.items():
                row = {}
                og, fixed = meta_dict["original"], meta_dict["fixed"]
                # If the file had no embedded metadata
                if og is None:
                    # Default all fields to None
                    for field_name in field_names:
                        row[field_name] = None
                # If the file had metadata
                else:
                    # Extract original and fixed metadata to write into row
                    for key in self.keys:
                        row[f"{key}_og"] = og.get(key, None)
                        row[f"{key}_fixed"] = fixed.get(key, None)
                # Save filepath for row
                row["file_path"] = f_path
                # Write row into result file
                writer.writerow(row)

        return True

    def run(self):
        """Main method to call all main methods of the MetaFixer class"""

        # If there are files to fix
        if self._get_files():
            # Extract, fix, and save fixed metadata
            self._fix_files()
            # Crete output fo fixing results
            self._output_results()


if __name__ == "__main__":
    fixer = MetaFixer()
    fixer.run()
