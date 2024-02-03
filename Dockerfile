FROM python:3.12.1
ENV PYTHONBUFFERD 1
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN apt-get update && \
    apt-get -y install ffmpeg libavcodec-extra && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
CMD ["python3","main.py"]
EXPOSE 8000
