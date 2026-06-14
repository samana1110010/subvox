import os
import unicodedata
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay


# =========================
# CONFIG
# =========================

DATA_DIR = "data"
MODE = "S2"

WORDS = ["Sim", "Nao", "Talvez"]
WORD_TO_IDX = {word: i for i, word in enumerate(WORDS)}
IDX_TO_WORD = {i: word for word, i in WORD_TO_IDX.items()}

CHANNELS = ["Channel_1", "Channel_2", "Channel_3", "Channel_4"]

MIN_SEGMENT_LENGTH = 30

# Every segment will become this length.
# If segment is shorter -> pad with zeros.
# If segment is longer -> truncate.
FIXED_LENGTH = 250

TEST_SIZE = 0.2
BATCH_SIZE = 8
EPOCHS = 50
LR = 0.001
RANDOM_STATE = 42

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# =========================
# REPRODUCIBILITY
# =========================

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


set_seed(RANDOM_STATE)


# =========================
# LABEL NORMALIZATION
# =========================

def normalize_word(text):
    text = str(text).strip().lower()
    text = text.replace("$", "")

    # converts "não" -> "nao"
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    return text


# =========================
# SEGMENT LOADING
# =========================

def load_segments_from_csv(word):
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

    if len(current_segment) >= MIN_SEGMENT_LENGTH:
        segments.append(np.array(current_segment, dtype=np.float32))

    lengths = [len(seg) for seg in segments]

    print(f"Extracted segments for {word}: {len(segments)}")
    print(f"min len: {min(lengths)} | max len: {max(lengths)} | avg len: {np.mean(lengths):.2f}")

    return segments


def normalize_segment(segment):
    """
    Normalize each channel inside one segment.
    segment shape: samples x channels
    """
    segment = segment.copy()

    for ch in range(segment.shape[1]):
        x = segment[:, ch]
        segment[:, ch] = (x - np.mean(x)) / (np.std(x) + 1e-8)

    return segment


def pad_or_truncate(segment, fixed_length=FIXED_LENGTH):
    """
    Input shape:
    samples x channels

    Output shape:
    fixed_length x channels
    """
    n, c = segment.shape

    if n > fixed_length:
        return segment[:fixed_length]

    if n < fixed_length:
        pad = np.zeros((fixed_length - n, c), dtype=np.float32)
        return np.vstack([segment, pad])

    return segment


def build_dataset():
    X = []
    y = []

    for word in WORDS:
        segments = load_segments_from_csv(word)

        for seg in segments:
            seg = normalize_segment(seg)
            seg = pad_or_truncate(seg, FIXED_LENGTH)

            X.append(seg)
            y.append(WORD_TO_IDX[word])

    X = np.array(X, dtype=np.float32)  # samples, time, channels
    y = np.array(y, dtype=np.int64)

    print("\n" + "=" * 60)
    print("FINAL DATASET")
    print("=" * 60)
    print("X shape:", X.shape)
    print("y shape:", y.shape)
    print("Labels:", {WORDS[i]: int(np.sum(y == i)) for i in range(len(WORDS))})

    return X, y


# =========================
# PYTORCH DATASET
# =========================

class EMGDataset(Dataset):
    def __init__(self, X, y, model_type):
        self.X = X
        self.y = y
        self.model_type = model_type

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        x = self.X[idx]  # time, channels

        if self.model_type == "1d":
            # Conv1D expects: channels, time
            x = np.transpose(x, (1, 0))  # channels, time

        elif self.model_type == "2d":
            # Conv2D expects: 1, channels, time
            x = np.transpose(x, (1, 0))  # channels, time
            x = np.expand_dims(x, axis=0)  # 1, channels, time

        else:
            raise ValueError("model_type must be '1d' or '2d'")

        return torch.tensor(x, dtype=torch.float32), torch.tensor(self.y[idx], dtype=torch.long)


# =========================
# MODELS
# =========================

class CNN1D(nn.Module):
    def __init__(self, num_classes=3):
        super().__init__()

        self.net = nn.Sequential(
            nn.Conv1d(4, 16, kernel_size=5, padding=2),
            nn.BatchNorm1d(16),
            nn.ReLU(),
            nn.MaxPool1d(2),

            nn.Conv1d(16, 32, kernel_size=5, padding=2),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.MaxPool1d(2),

            nn.Conv1d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU(),

            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),

            nn.Dropout(0.3),
            nn.Linear(64, num_classes)
        )

    def forward(self, x):
        return self.net(x)


class CNN2D(nn.Module):
    def __init__(self, num_classes=3):
        super().__init__()

        self.net = nn.Sequential(
            # input: batch, 1, 4, 250
            nn.Conv2d(1, 16, kernel_size=(2, 7), padding=(0, 3)),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=(1, 2)),

            nn.Conv2d(16, 32, kernel_size=(2, 5), padding=(0, 2)),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=(1, 2)),

            nn.Conv2d(32, 64, kernel_size=(1, 3), padding=(0, 1)),
            nn.BatchNorm2d(64),
            nn.ReLU(),

            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),

            nn.Dropout(0.3),
            nn.Linear(64, num_classes)
        )

    def forward(self, x):
        return self.net(x)


# =========================
# TRAINING + EVALUATION
# =========================

def train_model(model, train_loader, test_loader, title):
    model = model.to(DEVICE)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-4)

    print("\n" + "=" * 60)
    print(f"Training {title} on {DEVICE}")
    print("=" * 60)

    for epoch in range(1, EPOCHS + 1):
        model.train()
        total_loss = 0
        correct = 0
        total = 0

        for xb, yb in train_loader:
            xb = xb.to(DEVICE)
            yb = yb.to(DEVICE)

            optimizer.zero_grad()

            logits = model(xb)
            loss = criterion(logits, yb)

            loss.backward()
            optimizer.step()

            total_loss += loss.item() * len(xb)

            preds = torch.argmax(logits, dim=1)
            correct += (preds == yb).sum().item()
            total += len(xb)

        train_loss = total_loss / total
        train_acc = correct / total

        if epoch % 10 == 0 or epoch == 1:
            test_acc = get_accuracy(model, test_loader)
            print(
                f"Epoch {epoch:03d}/{EPOCHS} | "
                f"loss={train_loss:.4f} | "
                f"train_acc={train_acc:.4f} | "
                f"test_acc={test_acc:.4f}"
            )

    return model


def get_accuracy(model, loader):
    model.eval()
    correct = 0
    total = 0

    with torch.no_grad():
        for xb, yb in loader:
            xb = xb.to(DEVICE)
            yb = yb.to(DEVICE)

            logits = model(xb)
            preds = torch.argmax(logits, dim=1)

            correct += (preds == yb).sum().item()
            total += len(xb)

    return correct / total


def evaluate_model(model, loader, title):
    model.eval()

    y_true = []
    y_pred = []

    with torch.no_grad():
        for xb, yb in loader:
            xb = xb.to(DEVICE)

            logits = model(xb)
            preds = torch.argmax(logits, dim=1).cpu().numpy()

            y_pred.extend(preds)
            y_true.extend(yb.numpy())

    y_true_names = [IDX_TO_WORD[i] for i in y_true]
    y_pred_names = [IDX_TO_WORD[i] for i in y_pred]

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    print("\nClassification Report:")
    print(classification_report(y_true_names, y_pred_names, labels=WORDS, zero_division=0))

    cm = confusion_matrix(y_true_names, y_pred_names, labels=WORDS)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=WORDS)

    disp.plot()
    plt.title(title)
    plt.tight_layout()
    plt.show()


def run_experiment(X, y, model_type):
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y
    )

    train_ds = EMGDataset(X_train, y_train, model_type=model_type)
    test_ds = EMGDataset(X_test, y_test, model_type=model_type)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False)

    if model_type == "1d":
        model = CNN1D(num_classes=len(WORDS))
        title = "1D CNN - S-only segment classification"

    elif model_type == "2d":
        model = CNN2D(num_classes=len(WORDS))
        title = "2D CNN Channel-Time - S-only segment classification"

    else:
        raise ValueError("model_type must be '1d' or '2d'")

    model = train_model(model, train_loader, test_loader, title)
    evaluate_model(model, test_loader, title)


def main():
    print("Using device:", DEVICE)

    X, y = build_dataset()

    run_experiment(X, y, model_type="1d")
    run_experiment(X, y, model_type="2d")


if __name__ == "__main__":
    main()