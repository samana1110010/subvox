import os
import unicodedata
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay, accuracy_score

from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier


# =========================
# CONFIG
# =========================

DATA_DIR = "data"
MODE = "S"

WORDS = ["Sim", "Nao", "Talvez"]
CHANNELS = ["Channel_1", "Channel_2", "Channel_3", "Channel_4"]

MIN_SEGMENT_LENGTH = 30
NORMALIZE_SEGMENT = True

TEST_SIZE = 0.2
RANDOM_STATE = 42


# =========================
# TEXT NORMALIZATION
# =========================

def normalize_word(text):
    text = str(text).strip().lower()
    text = text.replace("$", "")

    # converts "não" -> "nao"
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    return text


# =========================
# FEATURE EXTRACTION
# =========================

def extract_features(segment):
    """
    segment shape = samples x channels

    One segment = one continuous word attempt/block.
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

        # simple percentiles sometimes help with noisy biosignals
        p25 = np.percentile(x, 25)
        p50 = np.percentile(x, 50)
        p75 = np.percentile(x, 75)

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
            p25,
            p50,
            p75,
            len(x)
        ])

    return features


# =========================
# SEGMENT LOADING
# =========================

def load_segments_from_csv(word):
    """
    Reads:
    data/S/Sim.csv
    data/S/Nao.csv
    data/S/Talvez.csv

    Detects continuous blocks where WORD == target word.

    Example:
    sim sim sim silence silence sim sim silence

    becomes:
    segment 1 = first sim block
    segment 2 = second sim block
    """

    path = os.path.join(DATA_DIR, MODE, f"{word}.csv")

    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing file: {path}")

    df = pd.read_csv(path)

    if "WORD" not in df.columns:
        raise ValueError(f"{path} does not have WORD column")

    expected = normalize_word(word)
    df["_WORD_NORM"] = df["WORD"].apply(normalize_word)

    missing = [ch for ch in CHANNELS if ch not in df.columns]
    if missing:
        raise ValueError(f"Missing channels in {path}: {missing}")

    print("\n" + "=" * 60)
    print(f"File: {path}")
    print("WORD counts:")
    print(df["WORD"].value_counts().head(20))

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

    # catch final segment
    if len(current_segment) >= MIN_SEGMENT_LENGTH:
        segments.append(np.array(current_segment, dtype=np.float32))

    lengths = [len(seg) for seg in segments]

    print(f"Extracted segments for {word}: {len(segments)}")

    if lengths:
        print(f"Segment lengths:")
        print(f"  min: {min(lengths)}")
        print(f"  max: {max(lengths)}")
        print(f"  avg: {np.mean(lengths):.2f}")
        print(f"  median: {np.median(lengths):.2f}")
    else:
        print("No valid segments found.")

    return segments


def build_dataset():
    X = []
    y = []

    segment_summary = {}

    for word in WORDS:
        segments = load_segments_from_csv(word)
        segment_summary[word] = [len(seg) for seg in segments]

        for seg in segments:
            X.append(extract_features(seg))
            y.append(word)

    X = np.array(X, dtype=np.float32)
    y = np.array(y)

    print("\n" + "=" * 60)
    print("FINAL SEGMENT SUMMARY")
    print("=" * 60)

    for word, lengths in segment_summary.items():
        if lengths:
            print(
                f"{word}: count={len(lengths)}, "
                f"min={min(lengths)}, "
                f"max={max(lengths)}, "
                f"avg={np.mean(lengths):.2f}"
            )
        else:
            print(f"{word}: count=0")

    print("\nDataset shape:")
    print("X:", X.shape)
    print("y:", y.shape)
    print("Labels:", np.unique(y, return_counts=True))

    return X, y


# =========================
# MODEL COMPARISON
# =========================

def get_models():
    return {
        "Random Forest": RandomForestClassifier(
            n_estimators=300,
            random_state=RANDOM_STATE,
            class_weight="balanced"
        ),

        "SVM RBF": make_pipeline(
            StandardScaler(),
            SVC(
                kernel="rbf",
                C=10,
                gamma="scale",
                class_weight="balanced"
            )
        ),

        "Logistic Regression": make_pipeline(
            StandardScaler(),
            LogisticRegression(
                max_iter=2000,
                class_weight="balanced"
            )
        ),

        "KNN": make_pipeline(
            StandardScaler(),
            KNeighborsClassifier(
                n_neighbors=5
            )
        ),

        "Gradient Boosting": GradientBoostingClassifier(
            random_state=RANDOM_STATE
        ),
    }


def plot_confusion_matrix(y_test, y_pred, title):
    cm = confusion_matrix(y_test, y_pred, labels=WORDS)

    disp = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=WORDS
    )

    disp.plot()
    plt.title(title)
    plt.tight_layout()
    plt.show()


def main():
    X, y = build_dataset()

    if len(X) == 0:
        raise ValueError("No data loaded. Check folder/files/WORD labels.")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y
    )

    print("\nTrain/Test split:")
    print("X_train:", X_train.shape)
    print("X_test :", X_test.shape)
    print("y_train:", np.unique(y_train, return_counts=True))
    print("y_test :", np.unique(y_test, return_counts=True))

    models = get_models()

    results = []

    for name, model in models.items():
        print("\n" + "=" * 60)
        print(f"Training model: {name}")
        print("=" * 60)

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        acc = accuracy_score(y_test, y_pred)
        results.append((name, acc))

        print(f"\nAccuracy: {acc:.4f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, labels=WORDS, zero_division=0))

        plot_confusion_matrix(
            y_test,
            y_pred,
            f"{name} - S-only segment classification"
        )

    print("\n" + "=" * 60)
    print("MODEL COMPARISON SUMMARY")
    print("=" * 60)

    results = sorted(results, key=lambda x: x[1], reverse=True)

    for name, acc in results:
        print(f"{name:25s} accuracy = {acc:.4f}")


if __name__ == "__main__":
    main()