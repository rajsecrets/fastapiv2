# Document Processing API

An API for processing and analyzing documents using Google's Gemini AI.

## Features

- Document classification
- Important details extraction
- Authenticity verification
- Support for PDF and image files

## API Endpoints

- `GET /`: Health check endpoint
- `POST /process-document/`: Process and analyze a document

## Local Development

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
5. Run the application:
   ```
   uvicorn main:app --reload
   ```

## Deployment

This application is set up for deployment on Render.

## Environment Variables

- `GEMINI_API_KEY`: Your Google Gemini API key (required)
- `PORT`: Port to run the application (defaults to 8000)
