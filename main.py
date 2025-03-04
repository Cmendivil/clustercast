from fastapi import FastAPI, HTTPException
from pybaseball import statcast_batter, playerid_lookup
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

app = FastAPI()


# Fetch player data from Statcast in real-time
def get_player_data(player_id: int, start_date: str, end_date: str):
    data = statcast_batter(start_date, end_date, player_id)
    return data



# Preprocess data
def preprocess_data(data):
    print(type(data))  # Inspect the columns
    features = ["launch_speed", "launch_angle", "barrel_pct", "hard_hit_pct"]
    # Filter features that exist in the DataFrame
    valid_features = [col for col in features if col in data.columns]
    print(f"Using features: {valid_features}")  # Print valid features
    data = data.dropna(subset=valid_features)
    scaler = StandardScaler()

    data.loc[:,valid_features] = scaler.fit_transform(data[valid_features])
    return data, valid_features


# Train K-Means model
def train_kmeans(data, features, num_clusters=10):
    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
    data["cluster"] = kmeans.fit_predict(data[features])
    return kmeans, data


@app.get("/similar_players/{player_name}")
def get_similar_players(player_name: str, num_results: int = 5):
    player_info = playerid_lookup(player_name.split()[1], player_name.split()[0])
    if player_info.empty:
        raise HTTPException(status_code=404, detail="Player not found")

    player_id = player_info.iloc[0]["key_mlbam"]
    player_data = get_player_data(player_id, "2020-03-01", "2024-03-03")  # Fetch recent data
    player_data, feature_cols = preprocess_data(player_data)
    kmeans_model, player_data = train_kmeans(player_data, feature_cols)

    # Ensure the player exists in the DataFrame
    if player_id not in player_data["batter"].values:
        raise HTTPException(status_code=404, detail="Player data not found in Statcast")

    player_cluster = player_data.loc[player_data["batter"] == player_id, "cluster"].values[0]
    print(f"Player {player_name} is in cluster {player_cluster}")
    print(f"Player Data - {player_data}")
    print(f"Player Data Cluster - {player_data["cluster"]}")
    print(f"Player Cluster - {player_cluster}")

    # Get similar players
    similar_players = player_data[player_data["cluster"] == player_cluster]
    print(f"similar_players - {similar_players}")
    print(f"similar_players[batter] - {similar_players["batter"]}")
    similar_players = similar_players[similar_players["batter"] != player_id]

    # Check how many similar players were found
    print(f"Found {len(similar_players)} similar players")

    return {"player_name": player_name, "similar_players": similar_players["player_name"].head(num_results).tolist()}

