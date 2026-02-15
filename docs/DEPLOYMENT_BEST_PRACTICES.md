# Deployment Best Practices

## Database Migrations Strategy

### Current Approach: Schema-First with Safety Net

The deployment uses a two-phase approach designed for both fresh installs and updates:

1. **Phase 1: Initialize Schema** - `create_db_and_tables()` creates all tables from current models
2. **Phase 2: Apply Migrations** - Alembic migrations handle schema changes with automatic fallback

### Why This Works

**For Fresh Installations:**
- `create_db_and_tables()` creates tables with current schema
- Migration attempt may fail if columns already exist
- Fallback automatically stamps migrations as current
- Result: Zero manual intervention required

**For Updates:**
- Existing database has older schema
- Migrations apply incrementally
- Each deployment adds only new changes
- Result: Smooth updates without downtime

### Migration File Guidelines

**DO:**
- ✅ Create migrations for schema changes to existing deployments
- ✅ Test migrations on both fresh and existing databases
- ✅ Use descriptive migration names

**DON'T:**
- ❌ Create migrations for columns that are already in models (redundant)
- ❌ Assume migrations will always succeed (use the fallback pattern)
- ❌ Delete old migration files (breaks existing deployments)

### Scaling to 100+ Deployments

The deployment script is designed for zero-touch installation:

```bash
# Single command deployment - no manual steps
~/chores_repo/scripts/deploy_release.sh main
```

**Automatic handling:**
- Database initialization
- Migration application with fallback
- Service installation and configuration
- User/path substitution
- Symlink management

**Result:** Clone, run script, reboot, done.

### Future Considerations

When adding new database columns or tables:

1. Add to models in `backend/models.py`
2. `create_db_and_tables()` will include them automatically
3. Create migration ONLY if updating existing deployments
4. Test on both fresh install and upgrade paths

### Troubleshooting

**"Duplicate column" error:**
- Expected on fresh installs when migration is redundant
- Deployment script handles this automatically
- No action needed

**Migration fails on update:**
- Check migration file syntax
- Verify column/table names match models
- Test migration in dev environment first
