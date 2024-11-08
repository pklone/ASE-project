FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./src/authentication.py ./

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python3", "authentication.py"] 
