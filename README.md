# ClusterCast API

This is the ClusterCast API, designed to find similar baseball players based on key performance metrics such as exit velocity, launch angle, and barrel percentage. This API can be used to analyze player data and make comparisons, which is especially useful for applications like fantasy leagues.

## Requirements

To run the ClusterCast API locally, you need to install the following dependencies:

- **Python 3.9+**
- **Uvicorn** for running the FastAPI app
- **FastAPI** for building the API
- **Boto3** for interacting with AWS DynamoDB
- **Mangum** for handling Lambda events (if deploying to AWS Lambda)
- **AWS CLI** for interacting with AWS services (e.g., configuring credentials, DynamoDB setup)
- **AWS account** to configure DynamoDB and set up AWS credentials

## Installation and Running Locally

Follow the steps below to set up and run the ClusterCast API locally:

### 1. Clone the repository

Clone the project repository to your local machine:

```bash
git clone https://github.com/Cmendivil/clustercast.git
cd clustercast
```

### 2. Create a Virtual Environment (Optional but Recommended)
It's recommended to use a virtual environment to isolate your dependencies:
```bash
python -m venv venv
source venv/bin/activate  # For Linux/macOS
venv\Scripts\activate     # For Windows
```

### 3. Install Dependencies
Install the required dependencies listed in requirements.txt:
```bash
pip install -r requirements.txt
pip install uvicorn
```

### 4. Set Up AWS DynamoDB
You need to set up an AWS DynamoDB table to store player data.

1. Go to the AWS Management Console.
2. Navigate to DynamoDB and create a new table with the following configurations:
   - Table Name: players
   - Primary Key: player_id (String)
3. Ensure you have data in your players table to query.
4. Make sure you set up AWS credentials by running:
```bash
aws configure
```

### 5. Create .env File
Create a .env file in the root of your project directory and add the following:
```bash
ORIGINS=your_origin_urls_here
```
Replace your_origin_urls_here with the allowed origins for your application, such as "http://localhost:3000".
### 6. Run the Application Locally
Once all dependencies are installed and your AWS DynamoDB is configured, you can run the FastAPI application locally:
```bash
uvicorn main:app --reload
```
This will start the API locally at http://127.0.0.1:8000.
### 7. Access the API Documentation
Once the server is running, you can access the API documentation by visiting:  
http://127.0.0.1:8000/docs  
This will open up the interactive API documentation where you can test the available endpoints directly from your browser.