FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies using PyPI index to avoid local mirror errors
COPY requirements.txt .
RUN pip install --no-cache-dir --index-url https://pypi.org/simple -r requirements.txt

# Copy application source code
COPY . .

# Set environment variables for Streamlit
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_BASE_URL_PATH=/closed-loop-admin
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["streamlit", "run", "admin_portal/app.py", "--server.baseUrlPath=/closed-loop-admin"]
