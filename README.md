# Quess ERP API

FastAPI-based ERP API for Quess assessment.

## Prerequisites

- Python 3.8+
- pip

## Setup
Git repo : https://github.com/abhijitkumarIN/quess-assesment-erp-api
Live instance url : http://quess.newsarmour.com/docs
1. **Create virtual environment**
```bash
python -m venv venv
```

2. **Activate virtual environment**

Windows:
```bash
venv\Scripts\activate
```

Linux/Mac:
```bash
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Copy `.env` file and update values as needed:
```
DATABASE_URL=sqlite:///./test_dbg.db
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_FROM=your_email@gmail.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com

## Run

fastapi dev main.py 

The API will be available at `http://localhost:8000`

API docs: `http://localhost:8000/docs`

## Features

- User authentication
- Employee management
- RESTful API endpoints
