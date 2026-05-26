Generic single-database configuration.



**How to create a migration with custom revision ID**

```bash
alembic revision --autogenerate -m '<migration message>' --rev-id "<migration revision name => date_message>"
```