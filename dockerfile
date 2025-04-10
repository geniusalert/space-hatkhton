# ===== Backend Stage =====
FROM ubuntu:22.04 as backend
RUN apt-get update && apt-get install -y python3 python3-pip
WORKDIR /app/backend
COPY backend/ /app/backend
RUN pip3 install -r requirements.txt

# ===== Frontend Stage =====
FROM ubuntu:22.04 as frontend
RUN apt-get update && apt-get install -y nodejs npm
WORKDIR /app/frontend
COPY frontend/src/ /app/frontend
RUN npm install

# ===== Final Stage =====
FROM ubuntu:22.04
# Copy backend
COPY --from=backend /app/backend /app/backend
# Copy frontend
COPY --from=frontend /app/frontend /app/frontend

# Install necessary runtime dependencies
RUN apt-get update && apt-get install -y python3 python3-pip nodejs npm

# Set working directory to backend by default
WORKDIR /app/backend

# Expose both ports
EXPOSE 8000
EXPOSE 3000

# Start both services using a shell script
CMD bash -c "cd /app/frontend && npm start & cd /app/backend && uvicorn app.main:app --host 0.0.0.0 --port 8000"
