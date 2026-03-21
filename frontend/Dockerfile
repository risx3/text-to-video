# Frontend development server for Docker Compose.
# For a production build, replace this with a multi-stage build that runs
# `npm run build` and serves the dist/ via nginx.

FROM node:20-alpine

WORKDIR /app

# Copy package manifests first for layer caching
COPY package.json package-lock.json* ./

RUN npm ci

# Copy source
COPY . .

EXPOSE 5173

# --host 0.0.0.0 makes the dev server reachable from outside the container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
