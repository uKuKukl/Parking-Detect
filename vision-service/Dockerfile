FROM ultralytics/ultralytics:latest-cpu

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VISION_MODEL_PATH=/app/vision/models/best.pt \
    VISION_OUTPUT_DIR=/app/vision/output

WORKDIR /app

COPY vision-service/requirements.txt /app/vision-service/requirements.txt
RUN pip install --no-cache-dir --timeout 300 --retries 5 -r /app/vision-service/requirements.txt

COPY vision-service /app/vision-service
COPY vision/decision_logic.py /app/vision/decision_logic.py
COPY vision/models /app/vision/models

WORKDIR /app/vision-service
EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
