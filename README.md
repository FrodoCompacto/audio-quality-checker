# Audio Frequency Analyzer for DJs

Analyze and validate the quality of your audio files in bulk, ensuring your music is ready for professional DJ performances.

---

## 🎵 Features

- Analyze **FLAC**, **AIFF**, **WAV**, **MP3**, and **M4A** files.
- Scans folders **recursively** (including subfolders).
- **Avoids reprocessing** files already analyzed using a file **hash** (not just the name).
- **Detects** maximum reliable frequency, bitrate, sample rate, bit depth, and duration.
- **Calculates a quality rating (0 to 100%)** based on technical parameters.
- **Generates a formatted Excel file** (`audio_analysis.xlsx`) with:
  - Conditional coloring: Green for high-quality tracks, Red for low-quality.
  - Highlights errors automatically.
- **Logs errors** separately in `errors.txt` for easy review.

---

## 🚀 How to Use

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/yourrepo.git
   cd yourrepo
   ```

2. **Install the requirements**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python src/analyze.py
   ```

4. **Select your music folder** when prompted.

5. **Check the results**:
   - `audio_analysis.xlsx` will be created/updated.
   - `errors.txt` will list any issues encountered.

---

## 📆 File Outputs

- **audio_analysis.xlsx**: Detailed report with color-coded ratings.
- **errors.txt**: Log file with errors and problematic tracks.
- **processed_state.json**: Internal tracking to skip already analyzed files.

---

## ⚙️ Requirements

- **Python 3.8+**
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

Note: These are just guidelines. Audio quality can be subjective depending on the equipment used and the specific needs of the event. Use your discretion when selecting tracks for a performance.

---

## 👓 How to Customize the Output

Inside `analyze.py`, you can configure these parameters to fit your needs:

### Configurable Parameters

```python
THRESH_DB = -60
```
- Threshold in decibels. Frequencies below this value are considered too weak to be meaningful.

```python
PROPORTION_THRESHOLD = 0.05
```
- Minimum proportion (5%) of the track that must exhibit energy at a frequency to consider it valid.

```python
N_FFT = 4096
```
- Size of the window used in the FFT (Fast Fourier Transform). Larger values provide higher frequency resolution but slower processing.

```python
STATE_FILE = 'processed_state.json'
```
- Name of the file that keeps track of which tracks have already been analyzed to avoid redundant work.

```python
EXCEL_FILE = 'audio_analysis.xlsx'
```
- Name of the generated Excel file containing the analysis results.

```python
ERROR_LOG_FILE = 'errors.txt'
```
- Name of the file where any errors during analysis will be recorded.

```python
WEIGHTS = {
    'freq': 40,
    'bitrate': 30,
    'samplerate': 20,
    'bitdepth': 10
}
```
- Defines how much each factor (frequency, bitrate, sample rate, bit depth) contributes to the overall quality rating.

You can adjust thresholds, file types, and how much each factor impacts the quality rating depending on your event requirements.

---

## 📄 License

This project is licensed under the **MIT License** — feel free to use, share, and modify.

# 🔥 Notes

- Only **new or changed** tracks are processed — saving time for large collections.
- Very useful for DJs ensuring **audio quality control** before gigs.

