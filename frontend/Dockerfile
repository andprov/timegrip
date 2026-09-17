FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN --mount=type=secret,id=seo_config \
    if [ -s /run/secrets/seo_config ]; then \
        export SEO_CONFIG=/run/secrets/seo_config; \
    fi && \
    npm run build


FROM nginx:stable-alpine AS runtime

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
