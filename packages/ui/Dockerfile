FROM node:22-alpine

WORKDIR /app

# The API address is built into the website, so it must be given at BUILD time.
# In Coolify: add NEXT_PUBLIC_API_URL as an environment variable and tick "Build Variable".
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

COPY packages/ui/package*.json ./
RUN npm ci

COPY packages/ui ./
RUN npm run build

ENV NODE_ENV=production
EXPOSE 3000

CMD ["npx", "next", "start", "-H", "0.0.0.0", "-p", "3000"]
