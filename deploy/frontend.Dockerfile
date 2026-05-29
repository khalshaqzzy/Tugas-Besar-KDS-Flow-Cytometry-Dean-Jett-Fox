FROM node:24-alpine AS build

WORKDIR /app

COPY app/frontend/package*.json ./
RUN npm ci

COPY app/frontend ./
RUN npm run build

FROM nginx:1.29-alpine

COPY deploy/nginx-frontend.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
