FROM dhi.io/node:24-alpine-dev AS build

WORKDIR /app

COPY package*.json .

RUN npm install

COPY . .

ENV NODE_OPTIONS="--max-old-space-size=4096"

RUN npm run build

FROM dhi.io/node:24-alpine AS prod

USER root

WORKDIR /app

COPY --from=build --chown=node:node /app/.output /app/.output

ENV NODE_ENV=production \
    TZ=Europe/Paris

USER node

EXPOSE 3000

CMD [ "node", ".output/server/index.mjs" ]