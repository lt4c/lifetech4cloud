# --- Base ---
FROM node:20-alpine AS base
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup -S app && adduser -S app -G app

# copy lock trước để cache
COPY package.json ./

# --- Deps ---
FROM base AS deps
RUN npm ci --omit=dev

# --- Runtime ---
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=deps /app/node_modules ./node_modules
# copy phần còn lại
COPY . .

USER app
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:'+(process.env.PORT||3000)+'/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"
EXPOSE 3000
CMD ["node","src/worker-server.js"]
