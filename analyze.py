import os
import json
import hashlib
import librosa
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
from mutagen import File as MutagenFile
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.formatting.rule import ColorScaleRule, CellIsRule

SUPPORTED_EXTENSIONS = ('.flac', '.aiff', '.aif', '.m4a', '.mp3', '.wav')
THRESH_DB = -60
PROPORTION_THRESHOLD = 0.05
N_FFT = 4096
STATE_FILE = 'processed_state.json'
EXCEL_FILE = 'audio_analysis.xlsx'
ERROR_LOG_FILE = 'errors.txt'

WEIGHTS = {
    'freq': 40,
    'bitrate': 30,
    'samplerate': 20,
    'bitdepth': 10
}

def log_error(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")

def load_state(path):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_state(path, state):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def file_hash(path, block_size=65536):
    hasher = hashlib.md5()
    try:
        with open(path, 'rb') as f:
            buf = f.read(block_size)
            while buf:
                hasher.update(buf)
                buf = f.read(block_size)
    except Exception as e:
        log_error(f"Hash generation error for {path}: {e}")
        return None
    return hasher.hexdigest()

def max_reliable_frequency(path, thresh_db=THRESH_DB, prop_thresh=PROPORTION_THRESHOLD):
    try:
        y, sr = librosa.load(path, sr=None, mono=True)
    except Exception as e:
        log_error(f"Audio load error {path}: {e}")
        return None, None
    S = np.abs(librosa.stft(y, n_fft=N_FFT))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=N_FFT)
    mags_db = librosa.amplitude_to_db(S, ref=np.max)
    presence = (mags_db > thresh_db).mean(axis=1)
    valid_bins = np.where(presence >= prop_thresh)[0]
    max_freq = float(freqs[valid_bins[-1]]) if valid_bins.size else 0.0
    return max_freq, sr

def compute_rating(freq, sr, bitrate, bitdepth):
    freq_score = min(freq / 20000.0, 1.0) * WEIGHTS['freq']
    br_score = min(bitrate / 320000.0, 1.0) * WEIGHTS['bitrate'] if bitrate else 0
    sr_score = min(sr / 48000.0, 1.0) * WEIGHTS['samplerate'] if sr else 0
    bd_score = min(bitdepth / 24.0, 1.0) * WEIGHTS['bitdepth'] if bitdepth else 0
    total = freq_score + br_score + sr_score + bd_score
    return round(total, 1)

def extract_metadata(filepath):
    try:
        f = MutagenFile(filepath)
        info = f.info
        bitrate = getattr(info, 'bitrate', None)
        samplerate = getattr(info, 'sample_rate', None)
        bitdepth = getattr(info, 'bits_per_sample', None)
        return bitrate, samplerate, bitdepth
    except Exception as e:
        log_error(f"Metadata extraction error {filepath}: {e}")
        return None, None, None

def scan_and_update(root_dir):
    state = load_state(STATE_FILE)
    updated = False

    files = [os.path.join(dp, f) for dp, _, files in os.walk(root_dir) for f in files
             if f.lower().endswith(SUPPORTED_EXTENSIONS)]
    total = len(files)
    count = 0

    for filepath in files:
        count += 1
        try:
            stat = os.stat(filepath)
        except Exception as e:
            log_error(f"Access error {filepath}: {e}")
            print(f"[{count}/{total}] Access error: {filepath}")
            continue

        h = file_hash(filepath)
        if not h:
            print(f"[{count}/{total}] Hash error: {filepath}")
            continue

        mtime = stat.st_mtime
        size = stat.st_size
        entry = state.get(h)
        if entry and entry.get('mtime') == mtime and entry.get('size') == size:
            print(f"[{count}/{total}] Already analyzed: {filepath}")
            continue

        freq, sr = max_reliable_frequency(filepath)
        bitrate, samplerate_meta, bitdepth = extract_metadata(filepath)

        try:
            duration = librosa.get_duration(filename=filepath)
        except Exception as e:
            log_error(f"Duration error {filepath}: {e}")
            duration = None

        rating = compute_rating(freq or 0, sr or 0, bitrate, bitdepth)

        entry_data = {
            'path': filepath,
            'mtime': mtime,
            'size': size,
            'duration': duration if duration is not None else 'ERROR',
            'freq': freq if freq is not None else 'ERROR',
            'bitrate': bitrate or 'N/A',
            'samplerate': samplerate_meta or 'N/A',
            'bitdepth': bitdepth or 'N/A',
            'rating': rating
        }
        state[h] = entry_data
        updated = True
        print(f"[{count}/{total}] Analyzed: {filepath} → {freq if freq else 'ERROR'} Hz, Rating: {rating}%")

    if updated:
        save_state(STATE_FILE, state)
        write_excel(state)
    else:
        print("No new or updated tracks found.")

def write_excel(state):
    wb = Workbook()
    ws = wb.active
    ws.title = "Audio Report"

    headers = ['file_name', 'file_size_bytes', 'duration_s', 'max_freq_hz',
               'bitrate', 'samplerate', 'bitdepth', 'rating']
    ws.append(headers)

    for e in state.values():
        filename = os.path.basename(e['path'])
        ws.append([
            filename, e['size'], round(e['duration'], 2) if isinstance(e['duration'], float) else e['duration'],
            e['freq'], e['bitrate'], e['samplerate'], e['bitdepth'], e['rating']
        ])

    header_font = Font(bold=True)
    for cell in ws[1]:
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')

    for column_cells in ws.columns:
        length = max(len(str(cell.value)) for cell in column_cells)
        ws.column_dimensions[column_cells[0].column_letter].width = length + 2

    rating_col = 'H'
    ws.conditional_formatting.add(
        f"{rating_col}2:{rating_col}{ws.max_row}",
        ColorScaleRule(start_type='num', start_value=0, start_color='FF0000',
                       mid_type='num', mid_value=50, mid_color='FFFF00',
                       end_type='num', end_value=100, end_color='00FF00')
    )

    error_fill = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')
    for col in ['C', 'D']:
        ws.conditional_formatting.add(
            f"{col}2:{col}{ws.max_row}",
            CellIsRule(operator='equal', formula=['"ERROR"'], fill=error_fill)
        )

    wb.save(EXCEL_FILE)
    print(f"\nExcel updated: {EXCEL_FILE}")

def select_folder_and_run():
    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title='Select audio folder')
    if not folder:
        messagebox.showinfo('Cancelled', 'No folder selected.')
        return
    scan_and_update(folder)
    messagebox.showinfo('Done', 'Analysis finished.')

if __name__ == '__main__':
    select_folder_and_run()
