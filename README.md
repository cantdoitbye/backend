Below is an example of a `README.md` that explains the configuration settings for your Django project. You can modify the descriptions as needed.

---

# Project Configuration Overview

This document provides an overview of the environment configuration settings used by the Django project. These settings configure Django, database connectivity, Neo4j, caching, task queue, email, object storage, and integration with a Matrix server.

> **Note:** Do not expose sensitive keys (such as `SECRET_KEY`, database passwords, etc.) in public repositories.

---

## Table of Contents

- [Django Settings](#django-settings)
- [Database Configuration](#database-configuration)
- [Neo4j Configuration](#neo4j-configuration)
- [Cache Configuration](#cache-configuration)
- [Celery Configuration](#celery-configuration)
- [Email Configuration](#email-configuration)
- [MinIO (S3) Storage Settings](#minio-s3-storage-settings)
- [Matrix Server Integration](#matrix-server-integration)
- [Additional Notes](#additional-notes)

---

## Django Settings

| Key                            | Description                                                                                             | Example Value                                               |
| ------------------------------ | ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| `SECRET_KEY`                   | A secret key for cryptographic signing. **Keep this secret in production!**                             | `django-insecure-cc0e&k14e15=cx9)xq+@i^^nv%g+#)t0*9wq9e2&-^p$z06d@(` |
| `DEBUG`                        | Flag to run Django in debug mode. Set to `False` in production.                                        | `True`                                                      |
| `IS_LOCAL_STATIC_STORAGE`      | Flag to indicate whether static storage is local.                                                     | `False`                                                     |
| `ENV`                          | The environment mode (e.g., development, production).                                                 | `development`                                               |

---

## Database Configuration

The project uses PostgreSQL as its database. The connection is specified via a URL.

| Key             | Description                                              | Example Value                                                                                            |
| --------------- | -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `DATABASE_URL`  | URL that defines the database connection.              | `postgresql://postgres:ooumphdatavault003@34.170.99.162:5432/postgres`                                     |

---

## Neo4j Configuration

This section configures connection settings for Neo4j using the [Neomodel](https://github.com/neo4j-contrib/neomodel) library.

| Key                                       | Description                                                                                  | Example Value                                                                                     |
| ----------------------------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `NEOMODEL_NEO4J_BOLT_URL`                   | URL to connect to the Neo4j instance using the Bolt protocol.                                | `bolt://neo4j:BwA4zwGhfRT8nx5@34.170.99.162:7687`                                                 |
| `NEOMODEL_SIGNALS`                        | Enables signals to automatically sync changes.                                             | `True`                                                                                            |
| `NEOMODEL_FORCE_TIMEZONE`                 | Forces Neo4j to use the specified timezone.                                                  | `False`                                                                                           |
| `NEOMODEL_MAX_CONNECTION_POOL_SIZE`         | Sets the maximum size of the connection pool.                                               | `5000`                                                                                            |

> **Note:** Alternative Neo4j connection strings are provided as comments for local development or alternate configurations.

---

## Cache Configuration

Redis is used for caching. The configuration below also serves as the configuration for the Celery message broker and result backend.

| Key         | Description                                                        | Example Value                                                         |
| ----------- | ------------------------------------------------------------------ | --------------------------------------------------------------------- |
| `REDIS_URL` | URL to connect to the Redis instance.                              | `redis://:ooumphmemoriDB003@34.170.99.162/0`                           |

---

## Celery Configuration

Celery is used for handling asynchronous tasks. Redis is configured as both the broker and result backend.

| Key                      | Description                                              | Example Value                                                         |
| ------------------------ | -------------------------------------------------------- | --------------------------------------------------------------------- |
| `CELERY_BROKER_URL`      | URL to connect to the Celery broker (Redis).             | `redis://:ooumphmemoriDB003@34.170.99.162/0`                           |
| `CELERY_RESULT_BACKEND`  | URL to store Celery task results (Redis).                | `redis://:ooumphmemoriDB003@34.170.99.162/0`                           |

---

## Email Configuration

The project uses Gmail's SMTP servers for sending email. There is also a commented out alternative email configuration.

| Key                     | Description                                                      | Example Value                        |
| ----------------------- | ---------------------------------------------------------------- | ------------------------------------ |
| `EMAIL_HOST`            | SMTP server host.                                                | `smtp.gmail.com`                     |
| `EMAIL_USE_TLS`         | Enable TLS for secure email sending.                             | `True`                               |
| `EMAIL_PORT`            | SMTP port to use.                                                | `587`                                |
| `EMAIL_HOST_USER`       | Email address used as the sender.                                | `noreply@ooumph.com`                 |
| `EMAIL_HOST_PASSWORD`   | Password or application-specific password for the email account. | `lfbjmwbqgxezbrnd`                   |

> **Important:** Never commit plain-text credentials to a public repository.

---

## MinIO (S3) Storage Settings

These settings configure MinIO, an S3-compatible object storage service, for storing media and static files.

| Key                                | Description                                                                 | Example Value                                                     |
| ---------------------------------- | --------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `AWS_ACCESS_KEY_ID`                | Access key for MinIO.                                                       | `bzzEogAhoFZtK1CP9UWu`                                             |
| `AWS_SECRET_ACCESS_KEY`            | Secret access key for MinIO.                                                | `rSUnflYkIrjy6O6B7DgbnB1hJMonn8TYtv4iK2yz`                         |
| `AWS_STORAGE_BUCKET_NAME`          | Bucket name where files will be stored.                                   | `ooumph`                                                          |
| `AWS_S3_ENDPOINT_URL`              | Endpoint URL for accessing the MinIO server.                              | `http://34.170.99.162:9000`                                         |
| `AWS_S3_CUSTOM_DOMAIN`             | Custom domain to access the storage bucket.                               | `34.170.99.162:9000/ooumph`                                         |
| `AWS_S3_CUSTOM_DOMAIN_MEDIA`       | Custom domain specifically for media files.                               | `34.170.99.162:9000/ooumph/media/`                                  |
| `AWS_QUERYSTRING_AUTH`             | Disable query string authentication in URLs.                             | `False`                                                           |

---

## Matrix Server Integration

The project includes integration with a Matrix server for real-time communications or notifications.

| Key                   | Description                                                                 | Example Value                                          |
| --------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------ |
| `MATRIX_SERVER_URL`   | URL of the Matrix server to connect to.                                     | `http://34.170.99.162:8008`                            |
| `MATRIX_RETRY_LIMIT`  | Maximum number of retry attempts when connecting to the Matrix server.      | `1`                                                  |
| `MATRIX_TIMEOUT`      | Timeout (in seconds) for each connection attempt to the Matrix server.      | `2`                                                  |

> **Note:** A commented out alternative server URL is provided for testing purposes.

---

## Additional Notes

- **Security:** Always protect sensitive credentials (e.g., keys, passwords) and avoid committing them into version control.
- **Environment:** Adjust the `DEBUG` and `ENV` settings appropriately for your deployment environment.
- **Local vs Production:** The configuration includes commented-out settings for local development. Make sure to update or remove these before deploying to production.
- **Documentation:** For more detailed information on each configuration option, please refer to the corresponding documentation (Django, PostgreSQL, Neo4j, Redis, Celery, Gmail SMTP, MinIO, Matrix).

---

## Location Search API

The project exposes a lightweight proxy for the Google Maps Places Text Search endpoint.

| Detail | Description |
| ------ | ----------- |
| Endpoint | `GET /service/location-search/` |
| Required | `query` – free-form text describing the place to search for |
| Optional | `language`, `region`, `type` – forwarded to Google Places Text Search |
| Response | Returns the JSON payload from Google Places |

### Configuration

- Set `GOOGLE_MAPS_API_KEY` in your environment so that `settings.GOOGLE_MAPS_API_KEY` is populated.
- The backend enforces a 5-second timeout and surfaces Google availability issues as HTTP 502.

### Example

```bash
curl "https://<your-host>/service/location-search/?query=coffee%20shops%20in%20Delhi&language=en"
```

---

By following this configuration guide, you should have a better understanding of how each component of the project is set up and how to modify settings based on your environment and deployment needs.

Shah Sanjay