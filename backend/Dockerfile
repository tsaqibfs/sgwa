FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
WORKDIR /app
COPY requirements.lock.txt ./
RUN pip install --no-cache-dir -r requirements.lock.txt \
    && useradd --uid 10001 --create-home app
COPY backend ./backend
COPY ml ./ml
COPY scripts/container_init.py ./scripts/container_init.py
RUN mkdir -p ml/artifacts && chown -R app:app ml/artifacts
USER app
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
