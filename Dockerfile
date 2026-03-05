FROM postgres:16

# Environment variables
ENV POSTGRES_DB=mydb
ENV POSTGRES_USER=admin
ENV POSTGRES_PASSWORD=admin123

# Expose PostgreSQL port
EXPOSE 5432
