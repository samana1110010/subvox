import os
import unicodedata
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay


# =========================
# CONFIG
# =========================

DATA_DIR = "data"

TRAIN_FOLDER = "S1"
TEST_FOLDER = "S2"

WORDS = ["Sim", "Nao", "Talvez"]

# Use only active channels first.
# In your earlier data, Channel_5 to Channel_8 were constant/dead.
CHANNELS = ["Channel_1", "Channel_2", "Channel_3", "Channel_4"]

WINDOW_SIZE = 250
STEP_SIZE = 250

NORMALIZE_WINDOWS = True


# =========================
# HELPER FUNCTIONS
# =========================

def normalize_word(text):
    """
    Normalizes labels.

    Examples:
    'não'      -> 'nao'
    'Nao'      -> 'nao'
    '$SILENCE' -> 'silence'
    ' talvez ' -> 'talvez'
    """
    text = str(text).strip().lower()
    text = text.replace("$", "")

    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    return text


def load_signal(folder, word):
    """
    Loads one CSV file from:

    data/S1/Sim.csv
    data/S1/Nao.csv
    data/S1/Talvez.csv

    or

    data/S2/Sim.csv
    data/S2/Nao.csv
    data/S2/Talvez.csv

    It keeps only the actual word rows and removes $SILENCE rows.
    """
    path = os.path.join(DATA_DIR, folder, f"{word}.csv")

    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing file: {path}")

    df = pd.read_csv(path)

    if "WORD" not in df.columns:
        raise ValueError(f"{path} does not have a WORD column")

    print(f"\nLoading: {path}")
    print("WORD counts:")
    print(df["WORD"].value_counts().head(10))

    expected = normalize_word(word)
    df["_WORD_NORM"] = df["WORD"].apply(normalize_word)

    # Keep only rows for the target word.
    # This removes $SILENCE rows.
    df = df[df["_WORD_NORM"] == expected]

    print(f"Rows after keeping only {word}: {len(df)}")

    if len(df) == 0:
        raise ValueError(
            f"No rows found for {word} in {path}. "
            f"Check WORD values in the CSV."
        )

    missing_channels = [ch for ch in CHANNELS if ch not in df.columns]
    if missing_channels:
        raise ValueError(f"Missing channels in {path}: {missing_channels}")

    signal = df[CHANNELS].apply(pd.to_numeric, errors="coerce").dropna()

    return signal.values.astype(np.float32)


def make_windows(signal, label):
    """
    Splits signal into fixed-size windows.

    Example:
    250 rows -> one window
    """
    X = []
    y = []

    for start in range(0, len(signal) - WINDOW_SIZE + 1, STEP_SIZE):
        window = signal[start:start + WINDOW_SIZE]
        X.append(window)
        y.append(label)

    return X, y


def extract_features(window):
    """
    Converts one EMG window into feature values.

    For each channel:
    - mean
    - standard deviation
    - RMS
    - mean absolute value
    - variance
    - waveform length
    - zero crossings
    """
    window = window.copy()

    if NORMALIZE_WINDOWS:
        for ch in range(window.shape[1]):
            x = window[:, ch]
            window[:, ch] = (x - np.mean(x)) / (np.std(x) + 1e-8)

    features = []

    for ch in range(window.shape[1]):
        x = window[:, ch]

        mean = np.mean(x)
        std = np.std(x)
        rms = np.sqrt(np.mean(x ** 2))
        mav = np.mean(np.abs(x))
        var = np.var(x)
        waveform_length = np.sum(np.abs(np.diff(x)))

        centered = x - np.mean(x)
        zero_crossings = np.sum(np.diff(np.sign(centered)) != 0)

        features.extend([
            mean,
            std,
            rms,
            mav,
            var,
            waveform_length,
            zero_crossings
        ])

    return features


def build_dataset(folder):
    """
    Builds the full dataset from one folder.

    Example:
    folder = S1

    Loads:
    data/S1/Sim.csv
    data/S1/Nao.csv
    data/S1/Talvez.csv
    """
    all_windows = []
    all_labels = []

    for word in WORDS:
        signal = load_signal(folder, word)
        windows, labels = make_windows(signal, word)

        print(f"{folder}/{word}: signal={signal.shape}, windows={len(windows)}")

        all_windows.extend(windows)
        all_labels.extend(labels)

    X = np.array([extract_features(w) for w in all_windows])
    y = np.array(all_labels)

    return X, y


# =========================
# MAIN EXPERIMENT
# =========================

def main():
    print("=" * 60)
    print(f"TRAIN FOLDER: {TRAIN_FOLDER}")
    print(f"TEST FOLDER : {TEST_FOLDER}")
    print("=" * 60)

    X_train, y_train = build_dataset(TRAIN_FOLDER)
    X_test, y_test = build_dataset(TEST_FOLDER)

    print("\nFinal shapes:")
    print("X_train:", X_train.shape)
    print("y_train:", y_train.shape)
    print("Train labels:", np.unique(y_train, return_counts=True))

    print("X_test:", X_test.shape)
    print("y_test:", y_test.shape)
    print("Test labels:", np.unique(y_test, return_counts=True))

    model = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        class_weight="balanced"
    )

    print("\nTraining Random Forest...")
    model.fit(X_train, y_train)

    print("Testing...")
    y_pred = model.predict(X_test)

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, labels=WORDS, zero_division=0))

    cm = confusion_matrix(y_test, y_pred, labels=WORDS)

    disp = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=WORDS
    )

    disp.plot()
    plt.title(f"Train {TRAIN_FOLDER}, Test {TEST_FOLDER}")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()