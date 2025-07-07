# mp3-metadata-fixer
Automated bulk-fixer for mp3 audio files with corrupt metadata due to character encoding issues, created for lunarfox27.

## Setup

1. Install the latest version of Python from [here](https://www.python.org/downloads/).
2. Install `uv` following the instructions [here](https://docs.astral.sh/uv/getting-started/installation/).
3. Download the code with `<>Code > Download ZIP` or clone the repository.
4. Either copy your music library to the `files` folder (feel free to delete the testing files) or set the location of your music library folder as follows:

    ```python
    # Assuming your music library folder is in "~/Music"
    if __name__ == "__main__":
        fixer = MetaFixer("~/Music")
        fixer.run()
    ```

5. Navigate to the location where the code has been downloaded using the command line.
6. Run `uv venv` to create a new virtual environment and run `uv install` to install the required dependencies.
7. Run the code using `uv run src/meta_fixer.py`

## Tips

For easier use, consider downloading an IDE like [VS Codium](https://vscodium.com/#install) to use a GUI instead of the command line.