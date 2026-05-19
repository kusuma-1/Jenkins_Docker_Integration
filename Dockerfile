FROM python
WORKDIR /newfol
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python","app.py"]
