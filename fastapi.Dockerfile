# 
FROM python:3.10.12

# 
WORKDIR /app

# 
# COPY ./.env /app/.env
COPY ./src /app/src
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/src/requirements.txt
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]

