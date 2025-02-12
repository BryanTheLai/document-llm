FROM python:3.11-slim-buster

WORKDIR /app

# Copy the requirements.txt file
COPY requirements.txt .

# Install dependencies using pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY src/app ./app
COPY src/main.py main.py

EXPOSE 8501

CMD ["streamlit", "run", "main.py", "--server.address=0.0.0.0"]