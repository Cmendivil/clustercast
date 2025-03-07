from decimal import Decimal, ROUND_HALF_UP
import os
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import boto3
from botocore.exceptions import ClientError
from pybaseball import cache
cache.enable("/tmp/pybaseball_cache")
from pybaseball import statcast_batter_exitvelo_barrels

# Fetch and merge statcast data for specified years
def fetch_and_merge_statcast_data(years: list):
    try:
        # Convert two-digit years to four-digit years
        years_4digit = [2000 + year if year < 100 else year for year in years]

        # Initialize the merged dataframe with the first year's data
        merged_df = statcast_batter_exitvelo_barrels(years_4digit[0])

        # Merge data for the remaining years
        for year, df in zip(years[1:], [statcast_batter_exitvelo_barrels(y) for y in years_4digit[1:]]):
            merged_df = pd.merge(merged_df, df, on=['last_name, first_name', 'player_id'],
                                 suffixes=(f'_{year - 1}', f'_{year}'))

        return merged_df
    except Exception as e:
        raise Exception(f"Error merging Statcast data: {str(e)}")


# Compute the weighted averages for the specified keys
def compute_weighted_averages(merged_df: pd.DataFrame, keys: list, years: list):
    try:
        print(merged_df.columns)
        for key in keys:
            w_avg = 0
            attempt = 0
            for year in years:
                w_avg += (merged_df[f'{key}_{year}'] * merged_df[f'attempts_{year}'])
                attempt += merged_df[f'attempts_{year}']
            merged_df[f'{key}_combined'] = w_avg / attempt
        return merged_df
    except Exception as e:
        raise Exception(f"Error computing weighted averages: {str(e)}")


# Feature scaling using StandardScaler
def scale_features(merged_df: pd.DataFrame, features: list):
    try:
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(merged_df[features])
        return scaled_features
    except Exception as e:
        raise Exception(f"Error scaling features: {str(e)}")


# Apply KMeans clustering
def apply_clustering(merged_df: pd.DataFrame, scaled_features: pd.DataFrame, num_clusters: int = 10):
    try:
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        merged_df['cluster'] = kmeans.fit_predict(scaled_features)
        return merged_df
    except Exception as e:
        raise Exception(f"Error applying KMeans clustering: {str(e)}")


# Insert data into DynamoDB
def insert_into_dynamodb(merged_df: pd.DataFrame, table_name: str):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')  # Change to your AWS region
    table = dynamodb.Table(table_name)
    ROUNDING_PRECISION = Decimal('0.01')

    try:
        for _, row in merged_df.iterrows():
            table.put_item(
                Item={
                    'player_id': str(row['player_id']),
                    'last_name': str(row['last_name, first_name']).split(",")[0],
                    'first_name': str(row['last_name, first_name']).split(",")[1],
                    'exit_velocity': Decimal(row['avg_hit_speed_combined']).quantize(ROUNDING_PRECISION,
                                                                                     rounding=ROUND_HALF_UP),
                    'launch_angle': Decimal(row['avg_hit_angle_combined']).quantize(ROUNDING_PRECISION,
                                                                                    rounding=ROUND_HALF_UP),
                    'brl_percent': Decimal(row['brl_percent_combined']).quantize(ROUNDING_PRECISION,
                                                                                 rounding=ROUND_HALF_UP),
                    'cluster': row['cluster'],
                }
            )
        print("Data successfully inserted into DynamoDB.")
    except ClientError as e:
        raise Exception(f"Error inserting data into DynamoDB: {e.response['Error']['Message']}")
    except Exception as e:
        raise Exception(f"Error inserting data into DynamoDB: {str(e)}")


def main():
    years = [21, 22, 23, 24]  # Example years to process (2-digit years)
    keys = ["avg_hit_angle", "avg_hit_speed", "brl_percent"]  # Example keys
    table_name = 'players'  # DynamoDB table name

    try:
        # Step 1: Fetch and merge statcast data
        merged_df = fetch_and_merge_statcast_data(years)

        # Step 2: Compute weighted averages
        merged_df = compute_weighted_averages(merged_df, keys, years)

        # Step 3: Scale features
        scaled_features = scale_features(merged_df,
                                         ['avg_hit_angle_combined', 'avg_hit_speed_combined', 'brl_percent_combined'])

        # Step 4: Apply clustering
        merged_df = apply_clustering(merged_df, scaled_features)

        # Step 5: Insert data into DynamoDB
        insert_into_dynamodb(merged_df, table_name)

    except Exception as e:
        print(f"Error in processing: {str(e)}")

