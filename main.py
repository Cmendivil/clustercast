from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import boto3
import json
import os
from mangum import Mangum
from botocore.exceptions import ClientError
from batch import main

app = FastAPI(
    title="ClusterCast API",
    description="Find similar hitters",
    version="1.0.0"
)

router = APIRouter()
load_dotenv()
origins = os.getenv("ORIGINS").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow specified origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

@router.get(
    "/get-players",
    responses={
        200: {
            "description": "List of players",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "player_id": "1",
                            "first_name": "John",
                            "last_name": "Doe"
                        },
                        {
                            "player_id": "2",
                            "first_name": "Jane",
                            "last_name": "Smith"
                        }
                    ]
                }
            }
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Error scanning DynamoDB: Unable to retrieve items."}
                }
            }
        }
    }
)
def get_players():
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')  # Replace with your AWS region
        table_name = 'players'  # Ensure this table exists in DynamoDB
        table = dynamodb.Table(table_name)

        # Scan the table and get selected attributes
        response = table.scan(
            ProjectionExpression="player_id, first_name, last_name"  # Specify the attributes to return
        )
        return response.get("Items", [])

    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Error scanning DynamoDB: {e.response['Error']['Message']}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@router.get(
    "/get-players/{player_id}",
    responses={
        200: {
            "description": "Player and similar players data",
            "content": {
                "application/json": {
                    "example": {
                        "player": {
                            "player_id": "1",
                            "first_name": "John",
                            "last_name": "Doe",
                            "brl_percent": 10.5,
                            "cluster": 3,
                            "exit_velocity": 89.4,
                            "launch_angle": 15.2
                        },
                        "similar": [
                            {
                                "player_id": "2",
                                "first_name": "Jane",
                                "last_name": "Smith",
                                "brl_percent": 9.8,
                                "cluster": 3,
                                "exit_velocity": 88.7,
                                "launch_angle": 16.0
                            },
                            {
                                "player_id": "3",
                                "first_name": "Mike",
                                "last_name": "Johnson",
                                "brl_percent": 10.0,
                                "cluster": 3,
                                "exit_velocity": 90.1,
                                "launch_angle": 14.5
                            }
                        ]
                    }
                }
            }
        },
        404: {
            "description": "Player not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Player not found"}
                }
            }
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Error querying DynamoDB: Unable to retrieve player data."}
                }
            }
        }
    }
)
def get_similar_players(player_id: str, num_results: int = 5):
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')  # Replace with your AWS region
        table_name = 'players'  # Ensure this table exists in DynamoDB
        table = dynamodb.Table(table_name)

        # Get the item for the specified player_id
        response = table.get_item(Key={"player_id": player_id})

        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Player not found")

        item = response["Item"]

        # Query for similar players
        query_response = table.query(
            IndexName="cluster-index",
            KeyConditionExpression="#cluster = :c",
            FilterExpression="player_id <> :player_id_value",
            ExpressionAttributeNames={
                "#cluster": "cluster"  # Replace 'cluster' with a placeholder name
            },
            ExpressionAttributeValues={
                ":c": item["cluster"],
                ":player_id_value": item["player_id"]
            },
            Limit=num_results
        )

        response = {
            "player": item,
            "similar": query_response.get("Items", [])
        }
        return response

    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Error querying DynamoDB: {e.response['Error']['Message']}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@router.get(
    "/doc",
    summary="API Documentation",
    description="Returns the OpenAPI documentation in JSON format.",
    responses={
        200: {
            "description": "Returns OpenAPI JSON documentation",
            "content": {
                "application/json": {
                    "example": {
                        "openapi": "3.0.0",
                        "info": {
                            "title": "ClusterCast API",
                            "description": "Find similar hitters",
                            "version": "1.0.0"
                        },
                        "paths": {
                            "/clustercast/get-players": {
                                "get": {
                                    "summary": "Get list of players",
                                    "description": "Returns a list of all players with `player_id`, `first_name`, and `last_name`."
                                }
                            },
                            "/clustercast/get-players/{player_id}": {
                                "get": {
                                    "summary": "Get player details and similar players",
                                    "description": "Fetches details of a specific player and returns similar players based on `cluster`."
                                }
                            }
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Internal server error: Unable to generate OpenAPI documentation"}
                }
            }
        }
    }
)
def doc():
    try:
        if not app.openapi():
            raise HTTPException(status_code=404, detail="Documentation not found")
        return app.openapi()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


app.include_router(router, prefix="/clustercast")

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")

    if 'httpMethod' in event:
        print("Processing API Gateway request")
        return Mangum(app)(event, context)

    if 'Records' in event:
        print("Processing batch job")
        return main()

    print("Unsupported event type")
    return {
        'statusCode': 400,
        'body': json.dumps('Unsupported event type')
    }
