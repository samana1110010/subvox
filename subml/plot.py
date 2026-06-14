import os
import unicodedata
import pandas as pd
import matplotlib.pyplot as plt

DATA_DIR = "data"
MODE = "F"
WORDS = ["Sim", "Nao", "Talvez"]
CHANNELS = ["Channel_1", "Channel_2", "Channel_3", "Channel_4"]

SAMPLES_TO_PLOT = 1500


def normalize_word(text):
    text = str(text).strip().lower()
    text = text.replace("$", "")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text


def load_word_signal(mode, word):
    path = os.path.join(DATA_DIR, mode, f"{word}.csv")
    df = pd.read_csv(path)

    df["_WORD_NORM"] = df["WORD"].apply(normalize_word)
    df = df[df["_WORD_NORM"] == normalize_word(word)]

    signal = df[CHANNELS].apply(pd.to_numeric, errors="coerce").dropna()
    return signal.reset_index(drop=True)


def plot_each_word():
    for word in WORDS:
        signal = load_word_signal(MODE, word)

        plt.figure(figsize=(12, 6))
        for ch in CHANNELS:
            plt.plot(signal[ch].iloc[:SAMPLES_TO_PLOT], label=ch)

        plt.title(f"{MODE} mode - {word} - first {SAMPLES_TO_PLOT} samples")
        plt.xlabel("Sample")
        plt.ylabel("Amplitude")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()


def plot_same_channel_all_words(channel="Channel_1"):
    plt.figure(figsize=(12, 6))

    for word in WORDS:
        signal = load_word_signal(MODE, word)
        plt.plot(signal[channel].iloc[:SAMPLES_TO_PLOT], label=word)

    plt.title(f"{MODE} mode - {channel} comparison across words")
    plt.xlabel("Sample")
    plt.ylabel("Amplitude")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_channel_means():
    means = {}

    for word in WORDS:
        signal = load_word_signal(MODE, word)
        means[word] = [signal[ch].mean() for ch in CHANNELS]

    plt.figure(figsize=(10, 5))

    x = range(len(CHANNELS))
    width = 0.25

    for i, word in enumerate(WORDS):
        positions = [p + i * width for p in x]
        plt.bar(positions, means[word], width=width, label=word)

    center_positions = [p + width for p in x]
    plt.xticks(center_positions, CHANNELS)
    plt.title(f"{MODE} mode - Mean amplitude per channel")
    plt.ylabel("Mean amplitude")
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    plot_each_word()

    for ch in CHANNELS:
        plot_same_channel_all_words(ch)

    plot_channel_means()