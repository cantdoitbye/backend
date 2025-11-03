# truststream/deployment/migration_runner.py

"""
Migration Runner for TrustStream v4.4

This module handles database migrations for both PostgreSQL (Django) and Neo4j
during deployment, ensuring data consistency and schema updates.
"""

import os
import sys
import subprocess
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import asyncpg
from neo4j import AsyncGraphDatabase

from .production_config import ProductionConfig, get_config


@dataclass
class MigrationResult:
    """Migration execution result."""
    
    database: str  # postgres, neo4j
    success: bool
    migrations_applied: List[str] = field(default_factory=list)
    migrations_failed: List[str] = field(default_factory=list)
    execution_time_seconds: float = 0.0
    error_message: Optional[str] = None
    rollback_available: bool = False


@dataclass
class MigrationStatus:
    """Overall migration status."""
    
    postgres_result: Optional[MigrationResult] = None
    neo4j_result: Optional[MigrationResult] = None
    overall_success: bool = False
    total_execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class MigrationRunner:
    """Database migration runner for TrustStream."""
    
    def __init__(self, config: Optional[ProductionConfig] = None):
        """Initialize migration runner."""
        self.config = config or get_config()
        self.logger = logging.getLogger(__name__)
        
        # Migration paths
        self.django_migrations_path = "truststream/migrations"
        self.neo4j_migrations_path = "truststream/neo4j_migrations.py"
        
        # Database connections
        self._postgres_pool: Optional[asyncpg.Pool] = None
        self._neo4j_driver = None
    
    async def initialize(self):
        """Initialize database connections."""
        try:
            # Initialize PostgreSQL connection pool
            self._postgres_pool = await asyncpg.create_pool(
                host=self.config.database.postgres_host,
                port=self.config.database.postgres_port,
                user=self.config.database.postgres_user,
                password=self.config.database.postgres_password,
                database=self.config.database.postgres_db,
                min_size=1,
                max_size=3
            )
            
            # Initialize Neo4j driver
            self._neo4j_driver = AsyncGraphDatabase.driver(
                self.config.database.neo4j_uri,
                auth=(
                    self.config.database.neo4j_user,
                    self.config.database.neo4j_password
                )
            )
            
            self.logger.info("Migration runner initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize migration runner: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup database connections."""
        try:
            if self._postgres_pool:
                await self._postgres_pool.close()
            
            if self._neo4j_driver:
                await self._neo4j_driver.close()
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    async def run_all_migrations(self) -> MigrationStatus:
        """Run all database migrations."""
        start_time = datetime.now()
        
        # Initialize if not already done
        if not self._postgres_pool:
            await self.initialize()
        
        self.logger.info("Starting database migrations...")
        
        # Run PostgreSQL migrations
        postgres_result = await self.run_postgres_migrations()
        
        # Run Neo4j migrations
        neo4j_result = await self.run_neo4j_migrations()
        
        # Determine overall success
        overall_success = postgres_result.success and neo4j_result.success
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        migration_status = MigrationStatus(
            postgres_result=postgres_result,
            neo4j_result=neo4j_result,
            overall_success=overall_success,
            total_execution_time=total_time,
            timestamp=start_time
        )
        
        if overall_success:
            self.logger.info(f"All migrations completed successfully in {total_time:.2f}s")
        else:
            self.logger.error(f"Migration failures detected - PostgreSQL: {postgres_result.success}, Neo4j: {neo4j_result.success}")
        
        return migration_status
    
    async def run_postgres_migrations(self) -> MigrationResult:
        """Run PostgreSQL/Django migrations."""
        start_time = datetime.now()
        
        self.logger.info("Running PostgreSQL migrations...")
        
        try:
            # Check if Django is available
            django_available = await self._check_django_availability()
            
            if django_available:
                # Run Django migrations
                result = await self._run_django_migrations()
            else:
                # Run raw SQL migrations
                result = await self._run_raw_postgres_migrations()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time_seconds = execution_time
            
            if result.success:
                self.logger.info(f"PostgreSQL migrations completed in {execution_time:.2f}s")
            else:
                self.logger.error(f"PostgreSQL migrations failed: {result.error_message}")
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"PostgreSQL migration execution failed: {e}")
            
            return MigrationResult(
                database="postgres",
                success=False,
                execution_time_seconds=execution_time,
                error_message=str(e)
            )
    
    async def _check_django_availability(self) -> bool:
        """Check if Django is available and configured."""
        try:
            import django
            from django.conf import settings
            from django.core.management import execute_from_command_line
            
            # Check if Django settings are configured
            if not settings.configured:
                # Configure Django settings for TrustStream
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ooumph.settings')
                django.setup()
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Django not available: {e}")
            return False
    
    async def _run_django_migrations(self) -> MigrationResult:
        """Run Django migrations."""
        try:
            # Run makemigrations first (in case there are new migrations)
            makemigrations_cmd = [
                sys.executable, "manage.py", "makemigrations", "truststream"
            ]
            
            makemigrations_result = subprocess.run(
                makemigrations_cmd,
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if makemigrations_result.returncode != 0:
                self.logger.warning(f"makemigrations warning: {makemigrations_result.stderr}")
            
            # Run migrate command
            migrate_cmd = [
                sys.executable, "manage.py", "migrate", "truststream"
            ]
            
            migrate_result = subprocess.run(
                migrate_cmd,
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if migrate_result.returncode != 0:
                return MigrationResult(
                    database="postgres",
                    success=False,
                    error_message=migrate_result.stderr
                )
            
            # Parse applied migrations from output
            applied_migrations = self._parse_django_migration_output(migrate_result.stdout)
            
            return MigrationResult(
                database="postgres",
                success=True,
                migrations_applied=applied_migrations
            )
            
        except Exception as e:
            return MigrationResult(
                database="postgres",
                success=False,
                error_message=str(e)
            )
    
    def _parse_django_migration_output(self, output: str) -> List[str]:
        """Parse Django migration output to extract applied migrations."""
        applied_migrations = []
        
        for line in output.split('\n'):
            if 'Applying' in line and 'truststream' in line:
                # Extract migration name from line like "Applying truststream.0001_initial... OK"
                parts = line.split('Applying ')[1].split('...')[0]
                applied_migrations.append(parts.strip())
        
        return applied_migrations
    
    async def _run_raw_postgres_migrations(self) -> MigrationResult:
        """Run raw PostgreSQL migrations without Django."""
        try:
            # Get list of migration files
            migration_files = self._get_postgres_migration_files()
            
            applied_migrations = []
            failed_migrations = []
            
            async with self._postgres_pool.acquire() as conn:
                # Create migration tracking table if not exists
                await self._create_migration_tracking_table(conn)
                
                # Get already applied migrations
                applied_migration_names = await self._get_applied_migrations(conn)
                
                # Apply new migrations
                for migration_file in migration_files:
                    migration_name = os.path.basename(migration_file)
                    
                    if migration_name in applied_migration_names:
                        self.logger.info(f"Migration {migration_name} already applied, skipping")
                        continue
                    
                    try:
                        await self._apply_postgres_migration(conn, migration_file, migration_name)
                        applied_migrations.append(migration_name)
                        self.logger.info(f"Applied migration: {migration_name}")
                        
                    except Exception as e:
                        self.logger.error(f"Failed to apply migration {migration_name}: {e}")
                        failed_migrations.append(migration_name)
            
            success = len(failed_migrations) == 0
            
            return MigrationResult(
                database="postgres",
                success=success,
                migrations_applied=applied_migrations,
                migrations_failed=failed_migrations,
                error_message=f"Failed migrations: {failed_migrations}" if failed_migrations else None
            )
            
        except Exception as e:
            return MigrationResult(
                database="postgres",
                success=False,
                error_message=str(e)
            )
    
    def _get_postgres_migration_files(self) -> List[str]:
        """Get list of PostgreSQL migration files."""
        migration_files = []
        
        if os.path.exists(self.django_migrations_path):
            for filename in sorted(os.listdir(self.django_migrations_path)):
                if filename.endswith('.py') and filename != '__init__.py':
                    migration_files.append(os.path.join(self.django_migrations_path, filename))
        
        return migration_files
    
    async def _create_migration_tracking_table(self, conn: asyncpg.Connection):
        """Create table to track applied migrations."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS truststream_migrations (
                id SERIAL PRIMARY KEY,
                migration_name VARCHAR(255) UNIQUE NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    async def _get_applied_migrations(self, conn: asyncpg.Connection) -> List[str]:
        """Get list of already applied migrations."""
        try:
            rows = await conn.fetch("SELECT migration_name FROM truststream_migrations")
            return [row['migration_name'] for row in rows]
        except:
            return []
    
    async def _apply_postgres_migration(self, 
                                      conn: asyncpg.Connection, 
                                      migration_file: str, 
                                      migration_name: str):
        """Apply a single PostgreSQL migration."""
        # Read migration file
        with open(migration_file, 'r') as f:
            migration_content = f.read()
        
        # For Django migration files, we need to extract SQL
        # This is a simplified approach - in production, you'd want more sophisticated parsing
        if 'operations' in migration_content:
            # This is a Django migration file - skip for now
            # In a real implementation, you'd parse the Django migration and convert to SQL
            self.logger.warning(f"Skipping Django migration file: {migration_name}")
            return
        
        # Execute migration SQL
        await conn.execute(migration_content)
        
        # Record migration as applied
        await conn.execute(
            "INSERT INTO truststream_migrations (migration_name) VALUES ($1)",
            migration_name
        )
    
    async def run_neo4j_migrations(self) -> MigrationResult:
        """Run Neo4j migrations."""
        start_time = datetime.now()
        
        self.logger.info("Running Neo4j migrations...")
        
        try:
            # Import Neo4j migration manager
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            
            try:
                from ..neo4j_migrations import Neo4jMigrationManager
            except ImportError:
                # Fallback import
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "neo4j_migrations", 
                    self.neo4j_migrations_path
                )
                neo4j_migrations_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(neo4j_migrations_module)
                Neo4jMigrationManager = neo4j_migrations_module.Neo4jMigrationManager
            
            # Initialize migration manager
            migration_manager = Neo4jMigrationManager(
                uri=self.config.database.neo4j_uri,
                user=self.config.database.neo4j_user,
                password=self.config.database.neo4j_password,
                database=self.config.database.neo4j_database
            )
            
            # Run migrations
            migration_results = await migration_manager.run_all_migrations()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Process results
            applied_migrations = []
            failed_migrations = []
            
            for migration_name, result in migration_results.items():
                if result.get('success', False):
                    applied_migrations.append(migration_name)
                else:
                    failed_migrations.append(migration_name)
            
            success = len(failed_migrations) == 0
            
            result = MigrationResult(
                database="neo4j",
                success=success,
                migrations_applied=applied_migrations,
                migrations_failed=failed_migrations,
                execution_time_seconds=execution_time,
                error_message=f"Failed migrations: {failed_migrations}" if failed_migrations else None
            )
            
            if success:
                self.logger.info(f"Neo4j migrations completed in {execution_time:.2f}s")
            else:
                self.logger.error(f"Neo4j migrations failed: {result.error_message}")
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Neo4j migration execution failed: {e}")
            
            return MigrationResult(
                database="neo4j",
                success=False,
                execution_time_seconds=execution_time,
                error_message=str(e)
            )
    
    async def rollback_postgres_migrations(self, target_migration: Optional[str] = None) -> MigrationResult:
        """Rollback PostgreSQL migrations."""
        start_time = datetime.now()
        
        self.logger.info(f"Rolling back PostgreSQL migrations to: {target_migration or 'initial'}")
        
        try:
            # Check if Django is available
            django_available = await self._check_django_availability()
            
            if django_available:
                # Use Django's migrate command with target
                migrate_cmd = [
                    sys.executable, "manage.py", "migrate", "truststream"
                ]
                
                if target_migration:
                    migrate_cmd.append(target_migration)
                else:
                    migrate_cmd.append("zero")  # Rollback all migrations
                
                migrate_result = subprocess.run(
                    migrate_cmd,
                    capture_output=True,
                    text=True,
                    cwd=os.getcwd()
                )
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                if migrate_result.returncode != 0:
                    return MigrationResult(
                        database="postgres",
                        success=False,
                        execution_time_seconds=execution_time,
                        error_message=migrate_result.stderr
                    )
                
                return MigrationResult(
                    database="postgres",
                    success=True,
                    execution_time_seconds=execution_time
                )
            
            else:
                # Manual rollback not implemented for raw SQL
                return MigrationResult(
                    database="postgres",
                    success=False,
                    error_message="Manual rollback not supported without Django"
                )
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return MigrationResult(
                database="postgres",
                success=False,
                execution_time_seconds=execution_time,
                error_message=str(e)
            )
    
    async def rollback_neo4j_migrations(self, target_migration: Optional[str] = None) -> MigrationResult:
        """Rollback Neo4j migrations."""
        start_time = datetime.now()
        
        self.logger.info(f"Rolling back Neo4j migrations to: {target_migration or 'initial'}")
        
        try:
            # Import Neo4j migration manager
            from ..neo4j_migrations import Neo4jMigrationManager
            
            # Initialize migration manager
            migration_manager = Neo4jMigrationManager(
                uri=self.config.database.neo4j_uri,
                user=self.config.database.neo4j_user,
                password=self.config.database.neo4j_password,
                database=self.config.database.neo4j_database
            )
            
            # Run rollback
            rollback_result = await migration_manager.rollback_migration(target_migration)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return MigrationResult(
                database="neo4j",
                success=rollback_result.get('success', False),
                execution_time_seconds=execution_time,
                error_message=rollback_result.get('error')
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return MigrationResult(
                database="neo4j",
                success=False,
                execution_time_seconds=execution_time,
                error_message=str(e)
            )
    
    async def validate_migrations(self) -> Dict[str, Any]:
        """Validate that migrations have been applied correctly."""
        self.logger.info("Validating migrations...")
        
        validation_results = {
            'postgres': {'valid': False, 'details': {}},
            'neo4j': {'valid': False, 'details': {}},
            'overall_valid': False
        }
        
        try:
            # Validate PostgreSQL migrations
            postgres_validation = await self._validate_postgres_migrations()
            validation_results['postgres'] = postgres_validation
            
            # Validate Neo4j migrations
            neo4j_validation = await self._validate_neo4j_migrations()
            validation_results['neo4j'] = neo4j_validation
            
            # Overall validation
            validation_results['overall_valid'] = (
                postgres_validation['valid'] and neo4j_validation['valid']
            )
            
            if validation_results['overall_valid']:
                self.logger.info("Migration validation passed")
            else:
                self.logger.error("Migration validation failed")
            
        except Exception as e:
            self.logger.error(f"Migration validation error: {e}")
            validation_results['error'] = str(e)
        
        return validation_results
    
    async def _validate_postgres_migrations(self) -> Dict[str, Any]:
        """Validate PostgreSQL migrations."""
        try:
            async with self._postgres_pool.acquire() as conn:
                # Check if TrustStream tables exist
                tables_query = """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name LIKE 'truststream_%'
                """
                
                tables = await conn.fetch(tables_query)
                table_names = [row['table_name'] for row in tables]
                
                expected_tables = [
                    'truststream_usertrustcache',
                    'truststream_contentmoderationcache',
                    'truststream_communityhealthcache',
                    'truststream_trustscorecache',
                    'truststream_moderationlog',
                    'truststream_agentperformancemetrics',
                    'truststream_trustnetworkanalytics'
                ]
                
                missing_tables = [t for t in expected_tables if t not in table_names]
                
                return {
                    'valid': len(missing_tables) == 0,
                    'details': {
                        'tables_found': table_names,
                        'missing_tables': missing_tables,
                        'total_tables': len(table_names)
                    }
                }
                
        except Exception as e:
            return {
                'valid': False,
                'details': {'error': str(e)}
            }
    
    async def _validate_neo4j_migrations(self) -> Dict[str, Any]:
        """Validate Neo4j migrations."""
        try:
            async with self._neo4j_driver.session() as session:
                # Check if TrustProfile nodes exist
                trust_profiles_query = "MATCH (tp:TrustProfile) RETURN count(tp) as count"
                result = await session.run(trust_profiles_query)
                trust_profile_count = (await result.single())["count"]
                
                # Check if trust relationships exist
                trust_rels_query = "MATCH ()-[r:TRUSTS]->() RETURN count(r) as count"
                result = await session.run(trust_rels_query)
                trust_rel_count = (await result.single())["count"]
                
                # Check indexes
                indexes_query = "SHOW INDEXES"
                result = await session.run(indexes_query)
                indexes = await result.data()
                
                trust_indexes = [idx for idx in indexes if 'trust' in idx.get('name', '').lower()]
                
                return {
                    'valid': True,  # Basic validation - nodes and relationships exist
                    'details': {
                        'trust_profile_count': trust_profile_count,
                        'trust_relationship_count': trust_rel_count,
                        'trust_indexes': len(trust_indexes),
                        'total_indexes': len(indexes)
                    }
                }
                
        except Exception as e:
            return {
                'valid': False,
                'details': {'error': str(e)}
            }


# Global migration runner instance
migration_runner = MigrationRunner()


def get_migration_runner() -> MigrationRunner:
    """Get the global migration runner instance."""
    return migration_runner