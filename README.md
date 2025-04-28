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
- **Select which audio formats** to analyze.
- Scans folders **recursively** (including subfolders).
- **Avoids reprocessing** files already analyzed using a file **hash**.
- **Reprocesses automatically** tracks that previously had errors.
- **Detects** maximum reliable frequency, bitrate, sample rate, bit depth, and duration.
- **Calculates a quality rating (0 to 100%)** based on technical parameters.
- **Generates a formatted Excel file** (`audio_analysis.xlsx`)
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

   If your .pyw files are properly associated with Python, you can simply double-click on the script file (`analyze.pyw`) to run it. The program will execute and prompt you to select the folder for analysis.

   For more control or if you encounter any issues, you can also run the script via the command line:
   ```bash
   python analyze.pyw
   ```

4. **Follow the application steps**:
   - Select the audio formats you want to analyze using the format selection window.
   - Choose the folder containing your tracks.

5. **Check the results**:
   - `audio_analysis.xlsx` will be created/updated.
   - `program.log` will list any issues encountered.

---

## 🔧 FFmpeg (Required for Full Compatibility)

This application **can start without FFmpeg**, but **many formats (especially MP3 and M4A) will not be analyzed correctly** without it.  
Without FFmpeg, **errors are guaranteed to occur** when processing some audio files — especially when reading duration, spectrum, or metadata.

**It is highly recommended to install or include FFmpeg** to ensure reliable and complete analysis.

If you want to use FFmpeg with this tool, follow the instructions below:

### Windows:

1. **Download FFmpeg**:
   - Visit [gyan.dev official website](https://www.gyan.dev/ffmpeg/builds/) and download the **ffmpeg-git-essentials.7z**.
   - Extract the archive and copy the `bin` folder to your project directory, i.e., `./ffmpeg/bin`.

   **Example folder structure**:
   ```
   /audio-quality-checker
   ├── analyze.pyw
   ├── requirements.txt
   ├── audio_analysis.xlsx
   ├── program.log
   ├── processed_state.json
   └── ffmpeg
       └── bin
           ├── ffmpeg.exe
           ├── ffprobe.exe
           └── other-ffmpeg-files
   ```

2. **Add FFmpeg to PATH (optional)**:
   - You can also add the FFmpeg folder to your system's PATH environment variable for global usage. In this case the program will recognize FFmpeg automatically, and it will not be necessary to install the standalone version in the project root.

### Linux:

1. **Install FFmpeg**:
   - On **Ubuntu/Debian** systems:
     ```bash
     sudo apt update
     sudo apt install ffmpeg
     ```
   - On **Fedora** systems:
     ```bash
     sudo dnf install ffmpeg
     ```
   - On **Arch Linux**:
     ```bash
     sudo pacman -S ffmpeg
     ```

2. **Using FFmpeg Standalone (optional)**:
   - If you want to use a local FFmpeg build, download the static build from [FFmpeg.org](https://ffmpeg.org/download.html).
   - Extract the `ffmpeg` folder to your project directory (e.g., `./ffmpeg/bin`).

Once FFmpeg is installed or included, the tool will automatically use it for better audio handling.

---

## 📁 File Outputs

- **audio_analysis.xlsx**: Detailed report.
- **program.log**: Log file with errors and other data.
- **processed_state.json**: Internal file.

---

## ⚙️ Requirements

- **Python 3.6+**
- Libraries:
  - `librosa`
  - `numpy`
  - `mutagen`
  - `openpyxl`
  - `tkinter` (comes with Python standard on most systems)

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

**Note**: These are just guidelines. Audio quality can be subjective depending on the equipment used and the specific needs of the event. Use your discretion when selecting tracks for a performance.

---

## ☝️🤓 How to Customize the Output

Inside `analyze.pyw`, you can configure these parameters to fit your needs:

### Configurable Parameters

```python
# Configurations
THRESH_DB = -60                        # Threshold in decibels. Frequencies below this value are considered too weak to be meaningful.
PROPORTION_THRESHOLD = 0.05            # Minimum proportion (5%) of the track that must exhibit energy at a frequency to consider it valid.
N_FFT = 4096                           # Size of the window used in the FFT (Fast Fourier Transform). Larger values provide higher frequency resolution but slower processing.
EXCEL_FILE = 'audio_analysis.xlsx'     # Name of the generated Excel file containing the analysis results.

WEIGHTS = {                            # Defines how much each factor (frequency, bitrate, sample rate, bit depth) contributes to the overall quality rating.
    'freq': 40,
    'bitrate': 30,
    'samplerate': 20,
    'bitdepth': 10
}
```

You can adjust thresholds, parameters, and how much each factor impacts the quality rating depending on your event requirements.

---

## 📄 License

This project is licensed under the **MIT License** — feel free to use, share, and modify.

---

## 🔥 Notes

- Only **new or changed** tracks are processed — saving time for large collections.
- Very useful for DJs ensuring **audio quality control** before gigs.
