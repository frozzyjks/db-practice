FROM python:3.11

WORKDIR /app

COPY src/task2/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "src.task2.parser"]