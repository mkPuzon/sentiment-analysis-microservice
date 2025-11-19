# Hugging Face Sentiment Analysis API

A robust REST API built with FastAPI that interfaces with Hugging Face Transformers to perform sentiment analysis. All incoming queries and their inference results are automatically logged to a PostgreSQL database.

The entire application is containerized using Docker for easy deployment and consistency.

### Tech Stack

Framework: FastAPI (Python 3.12.3)

Database: PostgreSQL (v15)

ORM: SQLAlchemy

ML Model: Hugging Face Transformers (distilbert-base-uncased-finetuned-sst-2-english)

Containerization: Docker & Docker Compose

## Getting Started

Clone the repository:

git clone [https://github.com/mkPuzon/sentiment-analysis-microservice.git](https://github.com/mkPuzon/sentiment-analysis-microservice.git)
cd sentiment-analysis-microservice


Configure Environment Variables:
Create a .env file in the root directory. You can copy the example below:

```
POSTGRES_USER=testuser
POSTGRES_PASSWORD=testpass
POSTGRES_DB=testdb
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgresql+psycopg2://testuser:testpass@db:5432/testdb
```


### Build and Run:
Run the application using Docker Compose. This will build the API image and pull the Postgres image.

docker-compose up --build


Note: The first run may take a minute as it downloads the PyTorch libraries and the Hugging Face model.

### API Usage

Once the container is running, the API is accessible at http://localhost:8000.

1. Interactive Documentation (Swagger UI)

Visit http://localhost:8000/docs to explore the endpoints and test them directly in your browser.

2. Query the Model

Send a POST request to the /query endpoint to analyze text.

Request:
```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"text": "This API is incredibly fast and useful!"}'
```

Response:

```bash
{
  "input_text": "This API is incredibly fast and useful!",
  "sentiment_label": "POSITIVE",
  "sentiment_score": 0.9998
}
```


## Database Schema

The application uses a simple schema to log requests. The query_logs table includes:
- id: Primary Key
- timestamp: When the query was made
- input_text: The user's query
- model_label: The result (POSITIVE/NEGATIVE)
- model_score: Confidence score (0.0 - 1.0)