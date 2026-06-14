import os
import random
import unicodedata
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay, accuracy_score


# ============================================================
# CONFIG
# ============================================================

DATA_DIR = "data"
MODE = "S"

WORDS = ["Sim", "Nao", "Talvez"]
WORD_TO_IDX = {word: i for i, word in enumerate(WORDS)}
IDX_TO_WORD = {i: word for word, i in WORD_TO_IDX.items()}

# Change to 1..9 if all 8 channels are active.
CHANNELS = ["Channel_1", "Channel_2", "Channel_3", "Channel_4"]
# CHANNELS = [f"Channel_{i}" for i in range(1, 9)]

MIN_SEGMENT_LENGTH = 30
FIXED_LENGTH = 250

TEST_SIZE = 0.2
BATCH_SIZE = 8
EPOCHS = 30
LR = 0.001
RANDOM_STATE = 42

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# ============================================================
# REPRODUCIBILITY
# ============================================================

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


set_seed(RANDOM_STATE)


# ============================================================
# LABEL NORMALIZATION
# ============================================================

def normalize_word(text):
    text = str(text).strip().lower()
    text = text.replace("$", "")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text


# ============================================================
# DATA LOADING
# ============================================================

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

    print("\n" + "=" * 70)
    print(f"File: {path}")
    print("WORD counts:")
    print(df["WORD"].value_counts().head(20))

    segments = []
    current_segment = []

    for _, row in df.iterrows():
        label = row["_WORD_NORM"]

        if label == expected:
            values = row[CHANNELS].apply(pd.to_numeric, errors="coerce").values.astype(np.float32)

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
    segment = segment.copy()

    for ch in range(segment.shape[1]):
        x = segment[:, ch]
        segment[:, ch] = (x - np.mean(x)) / (np.std(x) + 1e-8)

    return segment


def pad_or_truncate(segment, fixed_length=FIXED_LENGTH):
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
            seg = pad_or_truncate(seg)
            X.append(seg)
            y.append(WORD_TO_IDX[word])

    X = np.array(X, dtype=np.float32)  # samples, time, channels
    y = np.array(y, dtype=np.int64)

    print("\n" + "=" * 70)
    print("FINAL DATASET")
    print("=" * 70)
    print("X shape:", X.shape)
    print("y shape:", y.shape)
    print("Labels:", {WORDS[i]: int(np.sum(y == i)) for i in range(len(WORDS))})

    return X, y


# ============================================================
# SPECTROGRAM TRANSFORM
# ============================================================

def make_spectrogram(segment, n_fft=32, hop_length=8):
    """
    segment: time x channels

    Returns:
    channels x freq_bins x time_bins
    """

    x = torch.tensor(segment.T, dtype=torch.float32)  # channels x time

    spec = torch.stft(
        x,
        n_fft=n_fft,
        hop_length=hop_length,
        return_complex=True
    )

    spec = torch.abs(spec)  # channels x freq x time
    spec = torch.log1p(spec)

    return spec.numpy().astype(np.float32)


# ============================================================
# DATASET CLASS
# ============================================================

class EMGDataset(Dataset):
    def __init__(self, X, y, model_type):
        self.X = X
        self.y = y
        self.model_type = model_type

        if model_type == "spectrogram_2d":
            self.X_spec = np.array([make_spectrogram(x) for x in X], dtype=np.float32)
        else:
            self.X_spec = None

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        x = self.X[idx]  # time x channels

        if self.model_type == "1d":
            x = x.T  # channels x time

        elif self.model_type == "2d":
            x = x.T  # channels x time
            x = np.expand_dims(x, axis=0)  # 1 x channels x time

        elif self.model_type in ["cnn_lstm", "cnn_gru", "transformer"]:
            x = x.T  # channels x time

        elif self.model_type == "spectrogram_2d":
            # spectrogram shape = channels x freq x time
            x = self.X_spec[idx]

        else:
            raise ValueError(f"Unknown model_type: {self.model_type}")

        return torch.tensor(x, dtype=torch.float32), torch.tensor(self.y[idx], dtype=torch.long)


# ============================================================
# MODELS
# ============================================================

class CNN1D(nn.Module):
    def __init__(self, num_channels, num_classes):
        super().__init__()

        self.net = nn.Sequential(
            nn.Conv1d(num_channels, 16, kernel_size=5, padding=2),
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


class CNN2DChannelTime(nn.Module):
    def __init__(self, num_classes):
        super().__init__()

        self.net = nn.Sequential(
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


class CNNLSTM(nn.Module):
    def __init__(self, num_channels, num_classes):
        super().__init__()

        self.cnn = nn.Sequential(
            nn.Conv1d(num_channels, 32, kernel_size=5, padding=2),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.MaxPool1d(2),

            nn.Conv1d(32, 64, kernel_size=5, padding=2),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(2),
        )

        self.lstm = nn.LSTM(
            input_size=64,
            hidden_size=64,
            batch_first=True,
            bidirectional=True
        )

        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(128, num_classes)
        )

    def forward(self, x):
        # x: batch x channels x time
        x = self.cnn(x)             # batch x 64 x reduced_time
        x = x.permute(0, 2, 1)      # batch x reduced_time x 64

        out, _ = self.lstm(x)       # batch x reduced_time x 128
        last = out[:, -1, :]        # batch x 128

        return self.classifier(last)


class CNNGRU(nn.Module):
    def __init__(self, num_channels, num_classes):
        super().__init__()

        self.cnn = nn.Sequential(
            nn.Conv1d(num_channels, 32, kernel_size=5, padding=2),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.MaxPool1d(2),

            nn.Conv1d(32, 64, kernel_size=5, padding=2),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(2),
        )

        self.gru = nn.GRU(
            input_size=64,
            hidden_size=64,
            batch_first=True,
            bidirectional=True
        )

        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(128, num_classes)
        )

    def forward(self, x):
        # x: batch x channels x time
        x = self.cnn(x)             # batch x 64 x reduced_time
        x = x.permute(0, 2, 1)      # batch x reduced_time x 64

        out, _ = self.gru(x)        # batch x reduced_time x 128
        last = out[:, -1, :]        # batch x 128

        return self.classifier(last)


class TransformerEMG(nn.Module):
    def __init__(self, num_channels, num_classes):
        super().__init__()

        self.input_proj = nn.Linear(num_channels, 64)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=64,
            nhead=4,
            dim_feedforward=128,
            dropout=0.2,
            batch_first=True
        )

        self.encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=2
        )

        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(64, num_classes)
        )

    def forward(self, x):
        # x: batch x channels x time
        x = x.permute(0, 2, 1)      # batch x time x channels
        x = self.input_proj(x)      # batch x time x 64
        x = self.encoder(x)         # batch x time x 64
        x = x.mean(dim=1)           # batch x 64
        return self.classifier(x)


class SpectrogramCNN2D(nn.Module):
    def __init__(self, num_channels, num_classes):
        super().__init__()

        # input: batch x channels x freq x time
        self.net = nn.Sequential(
            nn.Conv2d(num_channels, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),

            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),

            nn.Dropout(0.3),
            nn.Linear(64, num_classes)
        )

    def forward(self, x):
        return self.net(x)


# ============================================================
# TRAINING + EVALUATION
# ============================================================

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


def train_model(model, train_loader, test_loader, title):
    model = model.to(DEVICE)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-4)

    best_test_acc = 0.0

    print("\n" + "=" * 70)
    print(f"Training: {title}")
    print(f"Device  : {DEVICE}")
    print("=" * 70)

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
        test_acc = get_accuracy(model, test_loader)

        best_test_acc = max(best_test_acc, test_acc)

        if epoch % 5 == 0 or epoch == 1:
            print(
                f"Epoch {epoch:03d}/{EPOCHS} | "
                f"loss={train_loss:.4f} | "
                f"train_acc={train_acc:.4f} | "
                f"test_acc={test_acc:.4f}"
            )

    print(f"Best test accuracy for {title}: {best_test_acc:.4f}")

    return model, best_test_acc


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

    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

    print("\nClassification Report:")
    print(classification_report(y_true_names, y_pred_names, labels=WORDS, zero_division=0))

    cm = confusion_matrix(y_true_names, y_pred_names, labels=WORDS)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=WORDS)

    disp.plot()
    plt.title(title)
    plt.tight_layout()
    plt.show()

    acc = accuracy_score(y_true_names, y_pred_names)

    return acc


# ============================================================
# RUN EXPERIMENTS
# ============================================================

def create_model(model_name):
    num_channels = len(CHANNELS)
    num_classes = len(WORDS)

    if model_name == "1D CNN":
        return CNN1D(num_channels, num_classes), "1d"

    if model_name == "2D CNN Channel-Time":
        return CNN2DChannelTime(num_classes), "2d"

    if model_name == "CNN + LSTM":
        return CNNLSTM(num_channels, num_classes), "cnn_lstm"

    if model_name == "CNN + GRU":
        return CNNGRU(num_channels, num_classes), "cnn_gru"

    if model_name == "Transformer Encoder":
        return TransformerEMG(num_channels, num_classes), "transformer"

    if model_name == "Spectrogram + 2D CNN":
        return SpectrogramCNN2D(num_channels, num_classes), "spectrogram_2d"

    raise ValueError(f"Unknown model name: {model_name}")


def run_one_model(model_name, X_train, X_test, y_train, y_test):
    model, model_type = create_model(model_name)

    train_ds = EMGDataset(X_train, y_train, model_type=model_type)
    test_ds = EMGDataset(X_test, y_test, model_type=model_type)

    train_loader = DataLoader(
        train_ds,
        batch_size=BATCH_SIZE,
        shuffle=True
    )

    test_loader = DataLoader(
        test_ds,
        batch_size=BATCH_SIZE,
        shuffle=False
    )

    model, best_acc = train_model(
        model,
        train_loader,
        test_loader,
        title=model_name
    )

    final_acc = evaluate_model(
        model,
        test_loader,
        title=f"{model_name} - S-only segment classification"
    )

    return best_acc, final_acc


def main():
    print("Using device:", DEVICE)
    print("Channels:", CHANNELS)

    X, y = build_dataset()

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
    print("Train labels:", {WORDS[i]: int(np.sum(y_train == i)) for i in range(len(WORDS))})
    print("Test labels :", {WORDS[i]: int(np.sum(y_test == i)) for i in range(len(WORDS))})

    model_names = [
        "1D CNN",
        "2D CNN Channel-Time",
        "CNN + LSTM",
        "CNN + GRU",
        "Transformer Encoder",
        "Spectrogram + 2D CNN",
    ]

    results = []

    for model_name in model_names:
        set_seed(RANDOM_STATE)

        best_acc, final_acc = run_one_model(
            model_name,
            X_train,
            X_test,
            y_train,
            y_test
        )

        results.append((model_name, best_acc, final_acc))

    print("\n" + "=" * 70)
    print("FINAL MODEL COMPARISON")
    print("=" * 70)
    print(f"{'Model':30s} {'Best Test Acc':>15s} {'Final Test Acc':>15s}")

    for name, best, final in sorted(results, key=lambda x: x[2], reverse=True):
        print(f"{name:30s} {best:15.4f} {final:15.4f}")


if __name__ == "__main__":
    main()