import pandas as pd

for mode in ["S"]:
    for word in ["Sim", "Nao", "Talvez"]:
        path = f"data/{mode}/{word}.csv"
        df = pd.read_csv(path)
        print("\n", path)
        print(df["WORD"].value_counts().head(20))