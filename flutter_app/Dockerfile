# Stage 1: Build the Flutter Web app
FROM debian:latest AS build-env

# Install dependencies
RUN apt-get update && apt-get install -y curl git wget unzip libgconf-2-4 gdb libstdc++6 libglu1-mesa fonts-droid-fallback lib32stdc++6 python3
RUN apt-get clean

# Download Flutter SDK
RUN git clone https://github.com/flutter/flutter.git /usr/local/flutter

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
# We can pass the base URL as a build argument
ARG API_BASE_URL=http://localhost:8000/api/v1
RUN sed -i "s|http://localhost:8000/api/v1|$API_BASE_URL|g" lib/services/api_service.dart
RUN flutter build web --release

# Stage 2: Serve the app with Nginx
FROM nginx:alpine
COPY --from=build-env /app/build/web /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
