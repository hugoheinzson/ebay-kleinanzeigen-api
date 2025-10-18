###############################################
# Frontend Multi-Stage Dockerfile (Next.js 14)
# - Handles missing public/ gracefully
# - Single npm ci (no duplicate install in runner)
# - Production node_modules pruning
# - Disables Next telemetry
###############################################

FROM node:20-bullseye-slim AS deps
WORKDIR /app

# Install exact dependencies
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

FROM node:20-bullseye-slim AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Ensure public exists even if not in repo (avoids COPY errors later)
RUN [ -d public ] || mkdir public

# Build Next.js app (can leverage experimental standalone later)
RUN npm run build

# Prune dev dependencies to reduce size for runner (keeps prod deps)
RUN npm prune --production

FROM node:20-bullseye-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Copy only what is needed for runtime
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.js ./next.config.js

# Optional: add a non-root user (commented out for simplicity)
# RUN useradd -m nextjs && chown -R nextjs:nextjs /app
# USER nextjs

EXPOSE 3000
CMD ["npm", "run", "start"]
