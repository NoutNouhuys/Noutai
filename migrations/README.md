# Database Migrations

This directory contains migration scripts for the Lynxx Anthropic Console database.

## Running Migrations

To apply migrations to your database, follow these steps:

1. Make sure your virtual environment is activated:
   ```
   source venv/bin/activate  # For Linux/Mac
   venv\Scripts\activate     # For Windows
   ```

2. If this is your first time running migrations, initialize the migrations repository:
   ```
   flask db init
   ```

3. Generate a migration script if you've made changes to your models:
   ```
   flask db migrate -m "Description of the changes"
   ```

4. Apply the migrations to your database:
   ```
   flask db upgrade
   ```

## Current Migrations

### Rename `metadata` to `message_metadata`

The `metadata` column in the `messages` table has been renamed to `message_metadata` to avoid conflicts with SQLAlchemy's reserved keywords. The migration script `rename_metadata_field.py` handles this change.

## Troubleshooting

If you encounter an error like the following when running `flask db init`:

```
sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
```

This is precisely the issue this migration fixes. You'll need to:

1. Manually modify the `models/conversation.py` file to rename the `metadata` field to `message_metadata`
2. Then initialize the database without the conflicting field name
3. Once the migration system is set up, you can apply the migration to existing databases
