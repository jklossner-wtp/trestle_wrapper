FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY trestle_app.py .
EXPOSE 8000
CMD ["uvicorn", "trestle_app:app", "--host", "0.0.0.0", "--port", "8000"]

