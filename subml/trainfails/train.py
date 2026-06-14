import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
from sklearn.model_selection import train_test_split


DATA_DIR = "data"
MODE = "S"  # "S" = subvocal, "F" = normal/full speech
WORDS = ["Sim", "Nao", "Talvez"]

# Use only active channels first.
# Your Channel_5 to Channel_8 looked constant/dead.
CHANNELS = ["Channel_1", "Channel_2", "Channel_3", "Channel_4"]

WINDOW_SIZE = 250
STEP_SIZE = 250  # no overlap for cleaner first experiment


import unicodedata

def normalize_word(text):
    text = str(text).strip().lower()
    text = text.replace("$", "")

    # converts "não" → "nao"
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    return text


def load_signal(path, expected_word):
    df = pd.read_csv(path)

    print("\nFile:", path)

    if "WORD" in df.columns:
        print("WORD counts:")
        print(df["WORD"].value_counts().head(20))

        expected_norm = normalize_word(expected_word)
        df["_WORD_NORM"] = df["WORD"].apply(normalize_word)

        # remove silence and keep only the target word
        df = df[df["_WORD_NORM"] == expected_norm]

        print(f"Rows after keeping only {expected_word}:", len(df))

    if len(df) == 0:
        raise ValueError(f"No rows left after filtering {path}. Check WORD values.")

    missing_channels = [ch for ch in CHANNELS if ch not in df.columns]
    if missing_channels:
        raise ValueError(f"Missing channels in {path}: {missing_channels}")

    signal = df[CHANNELS].apply(pd.to_numeric, errors="coerce")
    signal = signal.dropna()

    return signal.values.astype(np.float32)


def make_windows(signal, label):
    """
    Splits signal into fixed-size windows.

    signal shape:
    rows/samples x channels

    output:
    X = list of windows
    y = labels
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

    For every channel, calculate:
    - mean
    - std
    - RMS
    - mean absolute value
    - variance
    - waveform length
    - zero crossings
    """

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


def build_dataset(mode):
    all_windows = []
    all_labels = []

    for word in WORDS:
        path = os.path.join(DATA_DIR, mode, f"{word}.csv")

        print(f"\nLoading {word}: {path}")

        signal = load_signal(path, word)

        print(f"{word} signal shape after cleaning:", signal.shape)

        windows, labels = make_windows(signal, word)

        print(f"{word} windows:", len(windows))

        all_windows.extend(windows)
        all_labels.extend(labels)

    X_features = np.array([extract_features(w) for w in all_windows])
    y = np.array(all_labels)

    return X_features, y


def main():
    X, y = build_dataset(MODE)

    print("\nFinal dataset:")
    print("X shape:", X.shape)
    print("y shape:", y.shape)
    print("Labels:", np.unique(y, return_counts=True))

    if len(X) == 0:
        raise ValueError("No data found. Check CSV paths, WORD values, and channel names.")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        class_weight="balanced"
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    cm = confusion_matrix(y_test, y_pred, labels=WORDS)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=WORDS)
    disp.plot()
    plt.title(f"Random Forest Confusion Matrix - Mode {MODE}")
    plt.show()


if __name__ == "__main__":
    main()