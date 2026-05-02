FROM python:3.11

WORKDIR /app

COPY src/task2/requirements.txt requirements_task2.txt
COPY src/task3/requirements.txt requirements_task3.txt

RUN pip install --no-cache-dir -r requirements_task2.txt \
    && pip install --no-cache-dir -r requirements_task3.txt

COPY . .

CMD ["python", "-m", "src.task2.run"]