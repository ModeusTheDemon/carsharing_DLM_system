# ЭТАП 1: Сборка приложения через официальную JDK 24
FROM eclipse-temurin:24-jdk AS build
WORKDIR /app

# Копируем обертку Gradle из вашей папки проекта
COPY gradlew ./
COPY gradle gradle

# Копируем .kts файлы конфигурации сборки
COPY build.gradle.kts settings.gradle.kts ./

# Запускаем предварительное скачивание зависимостей и самого Gradle
RUN ./gradlew --no-daemon dependencies

# Копируем исходный код приложения
COPY src src

# Запускаем сборку JAR-файла
RUN ./gradlew --no-daemon bootJar -x test

# ЭТАП 2: Минимальный легковесный образ для запуска
FROM eclipse-temurin:24-jdk

WORKDIR /app
ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Устанавливаем curl для прохождения healthcheck в docker-compose
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Берем сгенерированный JAR из предыдущего этапа сборки
COPY --from=build /app/build/libs/*.jar app.jar

EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
