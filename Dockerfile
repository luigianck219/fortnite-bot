FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY fortnite_bot.py .

CMD ["python", "fortnite_bot.py"]
