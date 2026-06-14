import os
import unicodedata
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
from sklearn.model_selection import train_test_split


# =========================
# CONFIG
# =========================

DATA_DIR = "data"

WORDS = ["Sim", "Nao", "Talvez"]
CHANNELS = ["Channel_1", "Channel_2", "Channel_3", "Channel_4"]

MIN_SEGMENT_LENGTH = 30
NORMALIZE_SEGMENT = True


# =========================
# HELPERS
# =========================

def normalize_word(text):
    text = str(text).strip().lower()
    text = text.replace("$", "")

    # converts "não" -> "nao"
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    return text


def extract_features(segment):
    """
    segment shape = samples x channels
    One segment = one actual word attempt/block.
    """

    segment = segment.copy()

    if NORMALIZE_SEGMENT:
        for ch in range(segment.shape[1]):
            x = segment[:, ch]
            segment[:, ch] = (x - np.mean(x)) / (np.std(x) + 1e-8)

    features = []

    for ch in range(segment.shape[1]):
        x = segment[:, ch]

        mean = np.mean(x)
        std = np.std(x)
        rms = np.sqrt(np.mean(x ** 2))
        mav = np.mean(np.abs(x))
        var = np.var(x)
        waveform_length = np.sum(np.abs(np.diff(x)))

        centered = x - np.mean(x)
        zero_crossings = np.sum(np.diff(np.sign(centered)) != 0)

        maximum = np.max(x)
        minimum = np.min(x)
        peak_to_peak = maximum - minimum

        features.extend([
            mean,
            std,
            rms,
            mav,
            var,
            waveform_length,
            zero_crossings,
            maximum,
            minimum,
            peak_to_peak,
            len(x)
        ])

    return features


def load_segments_from_csv(mode, filename_word):
    """
    Reads:
    data/S/Sim.csv
    data/F/Sim.csv

    Extracts continuous blocks where WORD == target word.

    Example:
    sim sim sim silence silence sim sim silence
    becomes:
    segment 1 = first sim block
    segment 2 = second sim block
    """

    path = os.path.join(DATA_DIR, mode, f"{filename_word}.csv")

    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing file: {path}")

    df = pd.read_csv(path)

    if "WORD" not in df.columns:
        raise ValueError(f"{path} does not have WORD column")

    print(f"\nLoading: {path}")
    print("WORD counts:")
    print(df["WORD"].value_counts().head(20))

    expected = normalize_word(filename_word)
    df["_WORD_NORM"] = df["WORD"].apply(normalize_word)

    missing = [ch for ch in CHANNELS if ch not in df.columns]
    if missing:
        raise ValueError(f"Missing channels in {path}: {missing}")

    segments = []
    current_segment = []

    for _, row in df.iterrows():
        label = row["_WORD_NORM"]

        if label == expected:
            values = row[CHANNELS].apply(
                pd.to_numeric,
                errors="coerce"
            ).values.astype(np.float32)

            if not np.isnan(values).any():
                current_segment.append(values)
        else:
            if len(current_segment) >= MIN_SEGMENT_LENGTH:
                segments.append(np.array(current_segment, dtype=np.float32))
            current_segment = []

    if len(current_segment) >= MIN_SEGMENT_LENGTH:
        segments.append(np.array(current_segment, dtype=np.float32))

    print(f"Extracted {len(segments)} segments for {filename_word}")

    if len(segments) == 0:
        raise ValueError(f"No valid segments found for {filename_word} in {path}")

    return segments


def build_dataset(mode):
    X = []
    y = []

    for word in WORDS:
        segments = load_segments_from_csv(mode, word)

        lengths = [len(seg) for seg in segments]
        print(
            f"{mode}/{word}: "
            f"segments={len(segments)}, "
            f"min_len={min(lengths)}, "
            f"max_len={max(lengths)}, "
            f"avg_len={int(np.mean(lengths))}"
        )

        for seg in segments:
            X.append(extract_features(seg))
            y.append(word)

    X = np.array(X, dtype=np.float32)
    y = np.array(y)

    return X, y


def train_rf(X_train, y_train):
    model = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        class_weight="balanced"
    )
    model.fit(X_train, y_train)
    return model


def evaluate(model, X_test, y_test, title):
    y_pred = model.predict(X_test)

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, labels=WORDS, zero_division=0))

    cm = confusion_matrix(y_test, y_pred, labels=WORDS)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=WORDS)
    disp.plot()
    plt.title(title)
    plt.tight_layout()
    plt.show()


# =========================
# EXPERIMENT 1: S-only
# =========================

def experiment_s_only():
    print("\n\n==============================")
    print("EXPERIMENT 1: S-only")
    print("==============================")

    X, y = build_dataset("S")

    print("\nS dataset:")
    print("X:", X.shape)
    print("y:", y.shape)
    print("labels:", np.unique(y, return_counts=True))

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    model = train_rf(X_train, y_train)

    evaluate(
        model,
        X_test,
        y_test,
        "Segment-based RF: S-only train/test split"
    )


# =========================
# EXPERIMENT 2: F -> S
# =========================

def experiment_f_to_s():
    print("\n\n==============================")
    print("EXPERIMENT 2: Train F, Test S")
    print("==============================")

    X_train, y_train = build_dataset("F")
    X_test, y_test = build_dataset("S")

    print("\nTrain F dataset:")
    print("X_train:", X_train.shape)
    print("y_train:", y_train.shape)
    print("labels:", np.unique(y_train, return_counts=True))

    print("\nTest S dataset:")
    print("X_test:", X_test.shape)
    print("y_test:", y_test.shape)
    print("labels:", np.unique(y_test, return_counts=True))

    model = train_rf(X_train, y_train)

    evaluate(
        model,
        X_test,
        y_test,
        "Segment-based RF: Train F, Test S"
    )


def main():
    experiment_s_only()
    experiment_f_to_s()


if __name__ == "__main__":
    main()