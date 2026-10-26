# Imagen "web": compila con Node y sirve el resultado estatico con nginx.
# Node fijado en 22 (Vite 8 exige >= 22.12).
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY index.html vite.config.js ./
COPY src ./src
RUN npm run build

FROM nginx:1.30-alpine
# Parches de seguridad del sistema base publicados despues de la imagen (TASK-035, H-7).
RUN apk upgrade --no-cache
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
