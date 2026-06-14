import os
import unicodedata
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay


DATA_DIR = "data"

TRAIN_MODE = "F"   # train on full/normal speech
TEST_MODE = "S"    # test on subvocal

WORDS = ["Sim", "Nao", "Talvez"]
CHANNELS = ["Channel_1", "Channel_2", "Channel_3", "Channel_4"]

WINDOW_SIZE = 250
STEP_SIZE = 250

NORMALIZE_WINDOWS = True


def normalize_word(text):
    """
    Converts:
    'não' -> 'nao'
    '$SILENCE' -> 'silence'
    ' Talvez ' -> 'talvez'
    """
    text = str(text).strip().lower()
    text = text.replace("$", "")

    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    return text


def load_signal(mode, word):
    path = os.path.join(DATA_DIR, mode, f"{word}.csv")
    df = pd.read_csv(path)

    print(f"\nLoading {path}")

    if "WORD" not in df.columns:
        raise ValueError(f"{path} does not have WORD column")

    print("WORD counts:")
    print(df["WORD"].value_counts().head(10))

    expected = normalize_word(word)
    df["_WORD_NORM"] = df["WORD"].apply(normalize_word)

    # keep only target word, remove $SILENCE
    df = df[df["_WORD_NORM"] == expected]

    print(f"Rows after keeping only {word}:", len(df))

    if len(df) == 0:
        raise ValueError(f"No rows found for {word} in {path}")

    missing = [ch for ch in CHANNELS if ch not in df.columns]
    if missing:
        raise ValueError(f"Missing channels in {path}: {missing}")

    signal = df[CHANNELS].apply(pd.to_numeric, errors="coerce").dropna()

    return signal.values.astype(np.float32)


def make_windows(signal, label):
    X = []
    y = []

    for start in range(0, len(signal) - WINDOW_SIZE + 1, STEP_SIZE):
        window = signal[start:start + WINDOW_SIZE]
        X.append(window)
        y.append(label)

    return X, y


def extract_features(window):
    """
    Converts one EMG window into features.

    If NORMALIZE_WINDOWS=True, each channel is normalized inside each window.
    This reduces cheating through baseline differences.
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


def build_dataset(mode):
    all_windows = []
    all_labels = []

    for word in WORDS:
        signal = load_signal(mode, word)

        print(f"{mode}/{word} signal shape:", signal.shape)

        windows, labels = make_windows(signal, word)

        print(f"{mode}/{word} windows:", len(windows))

        all_windows.extend(windows)
        all_labels.extend(labels)

    X = np.array([extract_features(w) for w in all_windows])
    y = np.array(all_labels)

    return X, y


def main():
    print("\n==============================")
    print(f"TRAIN: {TRAIN_MODE}")
    print(f"TEST : {TEST_MODE}")
    print("==============================")

    X_train, y_train = build_dataset(TRAIN_MODE)
    X_test, y_test = build_dataset(TEST_MODE)

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

    print("\nTraining Random Forest on F...")
    model.fit(X_train, y_train)

    print("Testing on S...")
    y_pred = model.predict(X_test)

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    cm = confusion_matrix(y_test, y_pred, labels=WORDS)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=WORDS)
    disp.plot()
    plt.title("Train on F, Test on S - Random Forest")
    plt.show()


if __name__ == "__main__":
    main()