# Stage 1: Build the Flutter Web app
FROM debian:latest AS build-env

# Install dependencies
RUN apt-get update && apt-get install -y curl git wget unzip gdb libstdc++6 libglu1-mesa fonts-droid-fallback python3
RUN apt-get clean

# Download Flutter SDK
RUN git clone https://github.com/flutter/flutter.git /usr/local/flutter -b stable --depth 1

# Set flutter path
ENV PATH="/usr/local/flutter/bin:/usr/local/flutter/bin/cache/dart-sdk/bin:${PATH}"

# Run flutter doctor
RUN flutter doctor

# Enable web
RUN flutter config --enable-web

# Copy the app files
WORKDIR /app
COPY flutter_app/pubspec.yaml .
RUN flutter pub get
COPY flutter_app/ .

# Build the web app
ARG API_BASE_URL=http://localhost:8001/api/v1
RUN flutter build web --release --dart-define=API_BASE_URL=$API_BASE_URL

# Stage 2: Serve the app with Nginx
FROM nginx:alpine
COPY --from=build-env /app/build/web /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
