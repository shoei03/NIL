FROM openjdk:21-jdk-slim

WORKDIR /app

COPY . .

CMD ["bash"]