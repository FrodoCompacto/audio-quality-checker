import os
import sys
import json
import hashlib
import librosa
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
from mutagen import File as MutagenFile
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.formatting.rule import ColorScaleRule, CellIsRule
import logging
import traceback
import shutil
import time

# Attempt to include local FFmpeg (portable standalone) if present
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_FFMPEG = os.path.join(SCRIPT_DIR, 'ffmpeg', 'bin')
if os.path.isdir(LOCAL_FFMPEG):
    os.environ['PATH'] = LOCAL_FFMPEG + os.pathsep + os.environ.get('PATH', '')

# Configurations
SUPPORTED_EXTENSIONS = ['.flac', '.aiff', '.aif', '.m4a', '.mp3', '.wav']
THRESH_DB = -60
PROPORTION_THRESHOLD = 0.05
N_FFT = 4096
STATE_FILE = 'processed_state.json'
EXCEL_FILE = 'audio_analysis.xlsx'
LOG_FILE = 'program.log'

WEIGHTS = {
    'freq': 40,
    'bitrate': 30,
    'samplerate': 20,
    'bitdepth': 10
}

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger()

# Utility functions
def load_state(path):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            logger.exception(f"Error loading state from {path}")
    return {}

def save_state(path, state):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        logger.info(f"State saved to {path}")
    except Exception:
        logger.exception(f"Error saving state to {path}")

def file_hash(path, block_size=65536):
    hasher = hashlib.md5()
    try:
        with open(path, 'rb') as f:
            buf = f.read(block_size)
            while buf:
                hasher.update(buf)
                buf = f.read(block_size)
    except Exception:
        logger.exception(f"Hash generation error for {path}")
        return None
    return hasher.hexdigest()

def max_reliable_frequency(path):
    try:
        y, sr = librosa.load(path, sr=None, mono=True)
        S = np.abs(librosa.stft(y, n_fft=N_FFT))
        freqs = librosa.fft_frequencies(sr=sr, n_fft=N_FFT)
        mags_db = librosa.amplitude_to_db(S, ref=np.max)
        presence = (mags_db > THRESH_DB).mean(axis=1)
        valid_bins = np.where(presence >= PROPORTION_THRESHOLD)[0]
        max_freq = float(freqs[valid_bins[-1]]) if valid_bins.size else 0.0
        return max_freq, sr
    except Exception:
        logger.exception(f"Error analyzing frequency for {path}")
        return None, None

def extract_metadata(filepath):
    try:
        f = MutagenFile(filepath)
        info = f.info
        bitrate = getattr(info, 'bitrate', None)
        samplerate = getattr(info, 'sample_rate', None)
        bitdepth = getattr(info, 'bits_per_sample', None)
        return bitrate, samplerate, bitdepth
    except Exception:
        logger.exception(f"Metadata extraction error for {filepath}")
        return None, None, None

def compute_rating(freq, sr, bitrate, bitdepth):
    freq_score = min(freq / 20000.0, 1.0) * WEIGHTS['freq']
    br_score = min(bitrate / 320000.0, 1.0) * WEIGHTS['bitrate'] if bitrate else 0
    sr_score = min(sr / 48000.0, 1.0) * WEIGHTS['samplerate'] if sr else 0
    bd_score = 0
    active_weights = WEIGHTS['freq'] + WEIGHTS['bitrate'] + WEIGHTS['samplerate']
    if bitdepth:
        bd_score = min(bitdepth / 24.0, 1.0) * WEIGHTS['bitdepth']
        active_weights += WEIGHTS['bitdepth']
    raw = freq_score + br_score + sr_score + bd_score
    return round(raw / active_weights * 100, 1)

def needs_reanalysis(entry):
    if not entry:
        return True
    if any(str(entry.get(k)) in ("ERROR", "N/A", "None") for k in ['freq', 'duration', 'bitrate', 'samplerate']):
        return True
    return False

# Excel writer
def write_excel(state):
    wb = Workbook()
    ws = wb.active
    ws.title = "Audio Report"
    headers = ['file_name', 'file_size_bytes', 'duration_s', 'max_freq_hz',
               'bitrate', 'samplerate', 'bitdepth', 'rating']
    ws.append(headers)
    for e in state.values():
        ws.append([
            os.path.basename(e['path']),
            e['size'],
            round(e['duration'], 2) if isinstance(e['duration'], float) else e['duration'],
            e['freq'],
            e['bitrate'],
            e['samplerate'],
            e['bitdepth'],
            e['rating']
        ])
    # styling headers
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')
    # auto-fit columns
    for col in ws.columns:
        max_len = max(len(str(c.value)) for c in col)
        ws.column_dimensions[col[0].column_letter].width = max_len + 2
    # conditional formatting
    ws.conditional_formatting.add(
        f"H2:H{ws.max_row}",
        ColorScaleRule(start_type='num', start_value=0, start_color='FF0000',
                       mid_type='num', mid_value=50, mid_color='FFFF00',
                       end_type='num', end_value=100, end_color='00FF00')
    )
    error_fill = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')
    ws.conditional_formatting.add(
        f"C2:C{ws.max_row}", CellIsRule(operator='equal', formula=['"ERROR"'], fill=error_fill)
    )
    ws.conditional_formatting.add(
        f"D2:D{ws.max_row}", CellIsRule(operator='equal', formula=['"ERROR"'], fill=error_fill)
    )
    try:
        wb.save(EXCEL_FILE)
        return True
    except Exception:
        logger.exception(f"Failed to save Excel: {EXCEL_FILE}")
        return False

# GUI and main flow
def run_gui():
    # Check ffmpeg
    root = tk.Tk()
    root.withdraw()
    if not shutil.which('ffmpeg'):
        messagebox.showwarning('FFmpeg Not Found',
                               'FFmpeg was not found in PATH. For MP3/M4A support, please install FFmpeg.')
    # Extension selection window
    ext_win = tk.Toplevel()
    ext_win.title('Select Formats')
    tk.Label(ext_win, text='Check extensions to analyze:').pack(anchor='w', padx=10, pady=5)
    var_dict = {}
    for ext in SUPPORTED_EXTENSIONS:
        var = tk.BooleanVar(value=True)
        cb = tk.Checkbutton(ext_win, text=ext, variable=var)
        cb.pack(anchor='w', padx=20)
        var_dict[ext] = var
    def on_ext_ok():
        selected = [e for e, v in var_dict.items() if v.get()]
        ext_win.destroy()
        choose_folder_and_scan(selected)
    tk.Button(ext_win, text='OK', command=on_ext_ok).pack(pady=10)
    ext_win.protocol('WM_DELETE_WINDOW', sys.exit)
    root.mainloop()


def choose_folder_and_scan(selected_exts):
    folder = filedialog.askdirectory(title='Select audio folder')
    if not folder:
        messagebox.showinfo('Cancelled', 'No folder selected.')
        sys.exit()
    scan_and_update(folder, selected_exts)


def scan_and_update(folder, selected_exts):
    state = load_state(STATE_FILE)
    # gather files by selected extensions
    files = [os.path.join(dp, f)
             for dp, _, fs in os.walk(folder)
             for f in fs
             if os.path.splitext(f)[1].lower() in selected_exts]
    total = len(files)
    count = 0
    start_time = time.time()
    # build main window
    root = tk.Tk()
    root.title('Audio Analyzer')
    status_label = tk.Label(root, text='Preparing...')
    status_label.pack(pady=5)
    # count/total label
    count_label = tk.Label(root, text=f'0/{total}')
    count_label.pack(pady=2)
    progress = ttk.Progressbar(root, length=400, maximum=total)
    progress.pack(pady=5)
    eta_label = tk.Label(root, text='ETA: 0s')
    eta_label.pack(pady=5)

    def process_next():
        nonlocal count
        if count >= total:
            save_state(STATE_FILE, state)
            try:
                if write_excel(state):
                    messagebox.showinfo('Done', 'Analysis and report generated successfully.')
                else:
                    messagebox.showerror('Error',
                                         'Failed to save Excel report. JSON state was saved; you can regenerate Excel later.')
            except Exception:
                logger.exception('Unexpected error during Excel generation')
                messagebox.showerror('Error',
                                     'An unexpected error occurred while generating the Excel. Your analysis data is safe in the JSON state.')
            root.destroy()
            return
        filepath = files[count]
        count += 1
        # update UI
        status_label.config(text=f"Analyzing: {os.path.basename(filepath)}")
        count_label.config(text=f"{count}/{total}")
        progress['value'] = count
        elapsed = time.time() - start_time
        eta = int((elapsed / count) * (total - count)) if count else 0
        eta_label.config(text=f"ETA: {eta}s")
        root.update()
        # analysis
        try:
            stat = os.stat(filepath)
            mtime, size = stat.st_mtime, stat.st_size
            h = file_hash(filepath)
            entry = state.get(h)
            if not (entry and entry.get('mtime') == mtime and entry.get('size') == size and not needs_reanalysis(entry)):
                freq, sr = max_reliable_frequency(filepath)
                bitrate, samplerate_meta, bitdepth = extract_metadata(filepath)
                try:
                    duration = librosa.get_duration(filename=filepath)
                except Exception:
                    logger.exception(f"Duration error for {filepath}")
                    duration = 'ERROR'
                rating = compute_rating(freq or 0, sr or 0, bitrate, bitdepth)
                state[h] = {
                    'path': filepath,
                    'mtime': mtime,
                    'size': size,
                    'duration': duration,
                    'freq': freq if freq is not None else 'ERROR',
                    'bitrate': bitrate or 'N/A',
                    'samplerate': samplerate_meta or 'N/A',
                    'bitdepth': bitdepth or 'N/A',
                    'rating': rating
                }
        except Exception:
            logger.exception(f"Error processing {filepath}")
        root.after(10, process_next)

    root.after(100, process_next)
    root.mainloop()

if __name__ == '__main__':
    run_gui()
