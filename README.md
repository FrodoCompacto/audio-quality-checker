[![Python 3.6+](https://img.shields.io/badge/Python-3.6%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Work in Progress](https://img.shields.io/badge/Status-Work%20in%20Progress-orange)]()
[![Requirements](https://img.shields.io/badge/dependencies-low-lightgrey.svg)](requirements.txt)
[![Last Commit](https://img.shields.io/github/last-commit/FrodoCompacto/audio-quality-checker.svg)](https://github.com/FrodoCompacto/audio-quality-checker/commits/main)

# Audio Frequency Analyzer for DJs

Analyze and validate the quality of your audio files in bulk, ensuring your music is ready for professional DJ performances.

---

## 🎵 Features

- Analyze **FLAC**, **AIFF**, **WAV**, **MP3**, and **M4A** files.
- Scans folders **recursively** (including subfolders).
- **Avoids reprocessing** files already analyzed using a file **hash** and **mtime/size** checks.
- **Reprocesses automatically** tracks that previously had errors or format issues.
- **Detects** maximum reliable frequency, bitrate, sample rate, bit depth, and duration.
- **Calculates a quality rating (0 to 100%)** based on technical parameters.
- **Generates a formatted Excel file** (`audio_analysis.xlsx`).
- **Logs** in `program.log` for easy review.

---

## 🚀 How to Use

1. **Clone the repository**:
   ```bash
   git clone https://github.com/FrodoCompacto/audio-quality-checker
   cd audio-quality-checker
   ```

2. **Install the requirements**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:

   If your `.pyw` files are associated with Python, double-click `analyze.pyw`. Otherwise:
   ```bash
   python analyze.pyw
   ```

4. **Interact with the GUI**:
   - Click **Select Formats** to choose which extensions to include.
   - Click **Select Folder** and pick the directory to scan.

5. **Review outputs**:
   - `audio_analysis.xlsx` will be created/updated with the full report.
   - `program.log` will list any errors or warnings from processing.
   - `processed_state.json` stores internal state to skip unchanged files on subsequent runs.

---

## 🔧 FFmpeg (Required for Full Compatibility)

This application can start without FFmpeg, but many formats (especially MP3 and M4A) require it for correct analysis. Errors are likely without FFmpeg.

### Windows:

1. **Download FFmpeg**:
   - Get the **ffmpeg-git-essentials.7z** from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/).
   - Extract and place the `bin` folder under `./ffmpeg/bin` in the project.

2. **(Optional) Add FFmpeg to PATH** for system-wide usage.

### Linux:

1. **Install via package manager**:
   ```bash
   sudo apt update && sudo apt install ffmpeg   # Ubuntu/Debian
   sudo dnf install ffmpeg                      # Fedora
   sudo pacman -S ffmpeg                        # Arch Linux
   ```
2. **(Optional) Use a local build** by extracting the static build under `./ffmpeg/bin`.

Once FFmpeg is available, the tool auto-detects and leverages it for improved audio handling.

---

## 📁 File Outputs

- **audio_analysis.xlsx**: Detailed report with conditional formatting.
- **program.log**: Log file capturing errors and stack traces.
- **processed_state.json**: Internal JSON state for incremental runs.

---

## ⚙️ Requirements

- **Python 3.6+**
- Libraries:
  - `librosa`
  - `numpy`
  - `mutagen`
  - `openpyxl`
  - `tkinter` (standard)

---

## 📈 Rating System

The quality rating (0 to 100%) is calculated based on:
- Maximum reliable frequency detected.
- Bitrate of the file.
- Sampling rate.
- Bit depth (if available).

The rating is calculated based on technical parameters like frequency, bitrate, sample rate, and bit depth. Here's how you can interpret the results:

  - 80% or higher: The track is generally good enough for professional events and DJ performances. This rating indicates the track has a high enough quality for most shows and is suitable for high-quality sound systems.

  - 90% or higher: The track is considered excellent quality and would be perfect for events that require the best possible sound, such as large-scale concerts or professional DJ sets.

  - Below 80%: These tracks might have lower quality and may not sound as good on high-end audio systems. They might be acceptable for casual settings but are not recommended for professional performances.

Note: These are just guidelines. Audio quality can be subjective depending on the equipment used and the specific needs of the event. Use your discretion when selecting tracks for a performance.

---

## 🔥 How to Customize

Inside `analyze.pyw`, update these parameters to fine-tune analysis:

```python
THRESH_DB = -60                        # dB threshold for meaningful frequencies
PROPORTION_THRESHOLD = 0.05            # % of track momentum required per frequency bin
N_FFT = 4096                           # FFT window size (larger → finer spectral resolution, but slower)
MAX_WORKERS = 4                        # Number of concurrent threads
EXCEL_FILE = 'audio_analysis.xlsx'     # Output report
WEIGHTS = {                            # Weighting for rating factors
    'freq': 40,
    'bitrate': 30,
    'samplerate': 20,
    'bitdepth': 10
}
```

Adjust these to match your event requirements or hardware capabilities.

---

## 📄 License

This project is licensed under the **MIT License** — feel free to use, modify, and share.

