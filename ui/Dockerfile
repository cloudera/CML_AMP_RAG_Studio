FROM node:20-slim AS base
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable
COPY . /app
WORKDIR /app

FROM base AS server-deps
WORKDIR /app/express
RUN npm install --frozen-lockfile

FROM base AS frontend-deps
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --prod --frozen-lockfile

FROM base AS frontend-build
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --frozen-lockfile
RUN pnpm run build

FROM base AS e2e-tests
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install
RUN npx -y playwright@1.46.1 install --with-deps
RUN pnpm run e2e --reporter=dot

FROM docker-private.infra.cloudera.com/cloudera_base/ubi9/cldr-nodejs-20-minimal-cis:1-57-stig-31072024 AS rag_ui_final
COPY --from=frontend-deps /app/node_modules /app/node_modules
COPY --from=frontend-build /app/dist /app/dist
COPY --from=server-deps /app/express /app/express
COPY --from=server-deps /app/express/node_modules /app/express/node_modules

EXPOSE 3000
WORKDIR /app
CMD [ "node", "express/dist/index.js" ]
