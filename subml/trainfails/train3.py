#Train F + 10% S → Test 90% S
#   Checks if tiny S calibration helps.
import os
import unicodedata
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay


DATA_DIR = "data"

WORDS = ["Sim", "Nao", "Talvez"]
CHANNELS = ["Channel_1", "Channel_2", "Channel_3", "Channel_4"]

WINDOW_SIZE = 250
STEP_SIZE = 250

NORMALIZE_WINDOWS = True
S_CALIBRATION_RATIO = 0.10   # 10% S for calibration


def normalize_word(text):
    text = str(text).strip().lower()
    text = text.replace("$", "")

    # converts "não" -> "nao"
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    return text


def load_signal(mode, word):
    path = os.path.join(DATA_DIR, mode, f"{word}.csv")

    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing file: {path}")

    df = pd.read_csv(path)

    if "WORD" not in df.columns:
        raise ValueError(f"{path} does not have WORD column")

    expected = normalize_word(word)
    df["_WORD_NORM"] = df["WORD"].apply(normalize_word)

    # remove $SILENCE and keep only the actual word rows
    df = df[df["_WORD_NORM"] == expected]

    if len(df) == 0:
        raise ValueError(f"No rows found for {word} in {path}")

    missing_channels = [ch for ch in CHANNELS if ch not in df.columns]
    if missing_channels:
        raise ValueError(f"Missing channels in {path}: {missing_channels}")

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
    window = window.copy()

    # normalize each channel inside each window
    # this reduces cheating using only baseline voltage levels
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
        windows, labels = make_windows(signal, word)

        print(f"{mode}/{word}: signal shape = {signal.shape}, windows = {len(windows)}")

        all_windows.extend(windows)
        all_labels.extend(labels)

    X = np.array([extract_features(w) for w in all_windows])
    y = np.array(all_labels)

    return X, y


def build_s_calibration_and_test():
    """
    For each S word:
    - take first 10% windows for calibration/training
    - use remaining 90% windows for testing
    """

    X_calib_all = []
    y_calib_all = []

    X_test_all = []
    y_test_all = []

    for word in WORDS:
        signal = load_signal("S", word)
        windows, labels = make_windows(signal, word)

        X = np.array([extract_features(w) for w in windows])
        y = np.array(labels)

        n = len(X)
        calib_n = max(1, int(S_CALIBRATION_RATIO * n))

        X_calib = X[:calib_n]
        y_calib = y[:calib_n]

        X_test = X[calib_n:]
        y_test = y[calib_n:]

        print(f"S/{word}: total={n}, calibration={len(X_calib)}, test={len(X_test)}")

        X_calib_all.append(X_calib)
        y_calib_all.append(y_calib)

        X_test_all.append(X_test)
        y_test_all.append(y_test)

    X_calib_all = np.vstack(X_calib_all)
    y_calib_all = np.concatenate(y_calib_all)

    X_test_all = np.vstack(X_test_all)
    y_test_all = np.concatenate(y_test_all)

    return X_calib_all, y_calib_all, X_test_all, y_test_all


def main():
    print("\nExperiment: Train on F + 10% S, Test on remaining 90% S\n")

    # 1. Build full F training set
    X_f, y_f = build_dataset("F")

    # 2. Build 10% S calibration + 90% S test
    X_s_calib, y_s_calib, X_s_test, y_s_test = build_s_calibration_and_test()

    # 3. Combine F + 10% S for training
    X_train = np.vstack([X_f, X_s_calib])
    y_train = np.concatenate([y_f, y_s_calib])

    X_test = X_s_test
    y_test = y_s_test

    print("\nFinal shapes:")
    print("X_f:", X_f.shape)
    print("X_s_calib:", X_s_calib.shape)
    print("X_train:", X_train.shape)
    print("X_test:", X_test.shape)

    print("\nTrain labels:", np.unique(y_train, return_counts=True))
    print("Test labels:", np.unique(y_test, return_counts=True))

    # 4. Train model
    model = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        class_weight="balanced"
    )

    print("\nTraining...")
    model.fit(X_train, y_train)

    # 5. Test on remaining S
    print("Testing on remaining S...")
    y_pred = model.predict(X_test)

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, labels=WORDS, zero_division=0))

    cm = confusion_matrix(y_test, y_pred, labels=WORDS)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=WORDS)
    disp.plot()
    plt.title("Train on F + 10% S, Test on 90% S")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()