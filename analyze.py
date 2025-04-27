import os
import sys
import json
import hashlib
import librosa
import numpy as np
import logging
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
from mutagen import File as MutagenFile
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.formatting.rule import ColorScaleRule, CellIsRule

# Attempt to include local FFmpeg if present
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_FFMPEG = os.path.join(SCRIPT_DIR, 'ffmpeg', 'bin')
if os.path.isdir(LOCAL_FFMPEG):
    os.environ['PATH'] = LOCAL_FFMPEG + os.pathsep + os.environ.get('PATH', '')

# Configure logging: only warnings and errors
logging.basicConfig(
    filename='errors.txt',
    level=logging.WARNING,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger()

# Settings
SUPPORTED_EXTENSIONS = ('.flac', '.aiff', '.aif', '.m4a', '.mp3', '.wav')
THRESH_DB = -60
PROPORTION_THRESHOLD = 0.05
N_FFT = 4096
STATE_FILE = 'processed_state.json'
EXCEL_FILE = 'audio_analysis.xlsx'

WEIGHTS = {
    'freq': 40,
    'bitrate': 30,
    'samplerate': 20,
    'bitdepth': 10
}

def log_error(msg):
    logger.error(msg)


def load_state(path):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log_error(f"Failed to load state file: {e}")
    return {}


def save_state(path, state):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log_error(f"Failed to save state file: {e}")


def file_hash(path, block_size=65536):
    hasher = hashlib.md5()
    try:
        with open(path, 'rb') as f:
            while True:
                buf = f.read(block_size)
                if not buf:
                    break
                hasher.update(buf)
    except Exception as e:
        log_error(f"Hash error ({path}): {e}")
        return None
    return hasher.hexdigest()


def max_reliable_frequency(path):
    try:
        y, sr = librosa.load(path, sr=None, mono=True)
        if y is None or y.size == 0:
            raise ValueError('Empty audio buffer')
    except Exception as e:
        log_error(f"Audio load error ({path}): {e}")
        return None, None
    try:
        S = np.abs(librosa.stft(y, n_fft=N_FFT))
        freqs = librosa.fft_frequencies(sr=sr, n_fft=N_FFT)
        mags_db = librosa.amplitude_to_db(S, ref=np.max)
        presence = (mags_db > THRESH_DB).mean(axis=1)
        valid = np.where(presence >= PROPORTION_THRESHOLD)[0]
        max_freq = float(freqs[valid[-1]]) if valid.size else 0.0
        return max_freq, sr
    except Exception as e:
        log_error(f"Freq analysis error ({path}): {e}")
        return None, None


def extract_metadata(path):
    try:
        f = MutagenFile(path)
        info = f.info
        return (
            getattr(info, 'bitrate', None),
            getattr(info, 'sample_rate', None),
            getattr(info, 'bits_per_sample', None)
        )
    except Exception as e:
        log_error(f"Meta error ({path}): {e}")
        return None, None, None


def compute_rating(freq, sr, bitrate, bitdepth):
    fs = min(freq/20000.0,1.0)*WEIGHTS['freq']
    bs = min(bitrate/320000.0,1.0)*WEIGHTS['bitrate'] if bitrate else 0
    ss = min(sr/48000.0,1.0)*WEIGHTS['samplerate'] if sr else 0
    ds = 0
    w = WEIGHTS['freq']+WEIGHTS['bitrate']+WEIGHTS['samplerate']
    if bitdepth:
        ds = min(bitdepth/24.0,1.0)*WEIGHTS['bitdepth']
        w += WEIGHTS['bitdepth']
    return round((fs+bs+ss+ds)/w*100,1)


def scan_and_update(root):
    state = load_state(STATE_FILE)
    files = []
    for dp, _, fs in os.walk(root):
        for f in fs:
            if f.lower().endswith(SUPPORTED_EXTENSIONS):
                files.append(os.path.join(dp,f))
    total = len(files)
    changed=False

    for i, path in enumerate(files,1):
        try:
            st=os.stat(path)
        except Exception as e:
            log_error(f"Access error ({path}): {e}")
            continue
        h=file_hash(path)
        if not h: continue
        m,s=st.st_mtime,st.st_size
        prev=state.get(h)
        if prev and prev['mtime']==m and prev['size']==s \
           and prev['duration']!='ERROR' and prev['freq']!='ERROR':
            print(f"[{i}/{total}] Skip {path}")
            continue
        freq,sr=max_reliable_frequency(path)
        br,sr_meta,bd=extract_metadata(path)
        try:
            dur=librosa.get_duration(filename=path)
        except Exception as e:
            log_error(f"Duration error ({path}): {e}")
            dur='ERROR'
        rating=compute_rating(freq or 0,sr or 0,br,bd)
        state[h]={
            'path':path,'mtime':m,'size':s,
            'duration':round(dur,2) if isinstance(dur,float) else 'ERROR',
            'freq':round(freq,2) if freq!=None else 'ERROR',
            'bitrate':br or 'N/A','samplerate':sr_meta or 'N/A',
            'bitdepth':bd or 'N/A','rating':rating
        }
        changed=True
        print(f"[{i}/{total}] Analyzed {path} -> {state[h]['freq']}Hz, {rating}%")

    if changed:
        save_state(STATE_FILE,state)
        write_excel(state)
    else:
        print("No new or fixed tracks")


def write_excel(state):
    wb=Workbook();ws=wb.active;ws.title="Audio Report"
    hdrs=['file_name','file_size_bytes','duration_s','max_freq_hz',
          'bitrate','samplerate','bitdepth','rating']
    ws.append(hdrs)
    for e in state.values():
        ws.append([
            os.path.basename(e['path']),e['size'],e['duration'],
            e['freq'],e['bitrate'],e['samplerate'],e['bitdepth'],e['rating']
        ])
    for c in ws[1]: c.font=Font(bold=True);c.alignment=Alignment('center')
    for col in ws.columns:
        w=max(len(str(cell.value)) for cell in col)+2
        ws.column_dimensions[col[0].column_letter].width=w
    ws.conditional_formatting.add(
        f"H2:H{ws.max_row}",
        ColorScaleRule(0,'num','FF0000',50,'num','FFFF00',100,'num','00FF00')
    )
    ef=PatternFill('solid',start_color='FFC7CE',end_color='FFC7CE')
    for col in ['C','D']:
        ws.conditional_formatting.add(
            f"{col}2:{col}{ws.max_row}",
            CellIsRule('equal',['"ERROR"'],fill=ef)
        )
    try:
        wb.save(EXCEL_FILE)
        print(f"Excel saved: {EXCEL_FILE}")
    except Exception as e:
        log_error(f"Excel save error: {e}")


def select_folder_and_run():
    r=tk.Tk();r.withdraw()
    f=filedialog.askdirectory('Select audio folder')
    if not f: messagebox.showinfo('Cancelled','No folder selected');return
    scan_and_update(f)
    messagebox.showinfo('Done','Analysis finished')

if __name__=='__main__':
    select_folder_and_run()
