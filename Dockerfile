# Stage 1: Build the Application
FROM python:3.14-slim AS build

WORKDIR /usr/src/app

# Install system dependencies needed for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtual environment
RUN uv venv /opt/venv && \
    uv pip install --python /opt/venv/bin/python --no-cache -r pyproject.toml

# Copy the rest of the application source code
COPY . .

# Install the package itself
RUN uv pip install --python /opt/venv/bin/python --no-cache -e .


# Stage 2: Create the Final Production Image
FROM python:3.14-slim

WORKDIR /usr/src/app

# Install only runtime dependencies (libpq for psycopg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the build stage
COPY --from=build /opt/venv /opt/venv

# Copy the application code
COPY --from=build /usr/src/app .

# Set the virtual environment as the active Python environment
ENV PATH="/opt/venv/bin:$PATH"

# Create a non-root user to run the application
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /usr/src/app
USER appuser

# Define the command to start the bot
CMD ["python-italy-bot"]
