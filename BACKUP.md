# Database Backup & Recovery

## Backup Strategy

### Database Data Location
The PostgreSQL database data is stored in the user directory:
```
~/kleinanzeigen-database/
```

### Creating a Backup

#### Option 1: File System Backup (Recommended)
```bash
# Stop the database container
docker compose stop db

# Create a backup of the data directory
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz -C ~ kleinanzeigen-database

# Restart the database
docker compose start db
```

#### Option 2: PostgreSQL Dump (Alternative)
```bash
# Create a logical backup
docker compose exec db pg_dumpall -U kleinanzeigen > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restoring from Backup

#### Option 1: Restore from File System Backup
```bash
# Stop all containers
docker compose down

# Remove existing data
rm -rf ~/kleinanzeigen-database/*

# Extract backup
tar -xzf backup_YYYYMMDD_HHMMSS.tar.gz -C ~

# Start containers
docker compose up -d
```

#### Option 2: Restore from SQL Dump
```bash
# Stop containers and remove data
docker compose down
rm -rf ~/kleinanzeigen-database/*

# Start only the database
docker compose up -d db

# Wait for database to initialize, then restore
sleep 10
docker compose exec -T db psql -U kleinanzeigen -d kleinanzeigen < backup_YYYYMMDD_HHMMSS.sql

# Start all containers
docker compose up -d
```

### Automated Backup Script

Create a backup script for regular backups:

```bash
#!/bin/bash
# backup_db.sh

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Stop database for consistent backup
docker compose stop db

# Create backup
tar -czf "$BACKUP_DIR/kleinanzeigen_backup_$DATE.tar.gz" -C ~ kleinanzeigen-database

# Restart database
docker compose start db

# Keep only last 7 backups
ls -t $BACKUP_DIR/kleinanzeigen_backup_*.tar.gz | tail -n +8 | xargs rm -f

echo "Backup completed: $BACKUP_DIR/kleinanzeigen_backup_$DATE.tar.gz"
```

Make it executable:
```bash
chmod +x backup_db.sh
```

### Migration from Docker Volume

If you're migrating from the previous Docker volume setup:

```bash
# Stop containers
docker compose down

# Create data directory
mkdir -p ~/kleinanzeigen-database

# Copy data from Docker volume (if it exists)
docker run --rm -v postgres-data:/source -v ~/kleinanzeigen-database:/target alpine sh -c "cp -a /source/. /target/"

# Start with new configuration
docker compose up -d
```

## Security Notes

- The `~/kleinanzeigen-database/` directory contains sensitive database files
- Ensure proper file permissions are set
- Consider encrypting backups for production use
- Regular backup testing is recommended