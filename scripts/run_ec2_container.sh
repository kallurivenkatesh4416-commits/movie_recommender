#!/usr/bin/env sh
set -eu

: "${TMDB_API_KEY:?Set TMDB_API_KEY before running this script}"
: "${ECR_IMAGE:?Set ECR_IMAGE to your full ECR image URI}"

docker pull "$ECR_IMAGE"
docker stop movie-recommender || true
docker rm movie-recommender || true

docker run -d \
  --name movie-recommender \
  --restart unless-stopped \
  -p 8501:8501 \
  -e TMDB_API_KEY="$TMDB_API_KEY" \
  "$ECR_IMAGE"
