FROM python:3.10-slim

# Prophet's cmdstanpy backend needs a C++ toolchain to build CmdStan - the
# Linux equivalent of the RTools40 setup this project needed on Windows.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Build CmdStan once here, at image-build time, so it isn't rebuilt (slowly,
# fragile-ly) on every container start.
RUN python -c "import cmdstanpy; cmdstanpy.install_cmdstan()"

COPY . .
RUN mkdir -p data/uploads

# Bake a seeded, metrics-calculated database into the IMAGE at build time.
# The container's filesystem is ephemeral once running - anything written
# at runtime disappears on the next restart - but anything written during
# the build becomes part of the image itself, so every fresh container
# starts from this populated snapshot instead of an empty database.
RUN python -m app.services.data_generator
RUN python -m app.scripts.recalculate_metrics

# Build the RAG knowledge index from the committed, already-embedded
# app/knowledge/embeddings.json - no API keys needed at build time, and it
# fails loudly if the corpus and embeddings.json have drifted apart.
RUN python -m app.scripts.build_knowledge_index

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
