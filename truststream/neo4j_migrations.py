# truststream/neo4j_migrations.py

"""
TrustStream Neo4j Migration Utilities

This module provides utilities for managing Neo4j schema updates and data migrations
for TrustStream integration. It handles creating new node types, relationships,
indexes, and constraints required for TrustStream functionality.

Key Features:
- Schema migration management
- Index and constraint creation
- Data migration utilities
- Rollback capabilities
- Migration validation
"""

from neomodel import db, config
from datetime import datetime
import logging
import json
from typing import List, Dict, Any, Optional


logger = logging.getLogger(__name__)


class Neo4jMigrationManager:
    """
    Manager for Neo4j schema migrations and data updates for TrustStream.
    
    This class provides a structured approach to managing Neo4j database
    schema changes and data migrations for TrustStream integration.
    """
    
    def __init__(self):
        self.migration_history = []
        self.current_version = "1.0.0"
    
    def run_all_migrations(self) -> bool:
        """
        Run all TrustStream Neo4j migrations in order.
        
        Returns:
            bool: True if all migrations succeeded, False otherwise
        """
        migrations = [
            self.create_truststream_indexes,
            self.create_truststream_constraints,
            self.create_trust_relationships,
            self.migrate_existing_user_data,
            self.migrate_existing_post_data,
            self.migrate_existing_community_data,
            self.create_trust_profiles,
            self.initialize_trust_network,
        ]
        
        for migration in migrations:
            try:
                logger.info(f"Running migration: {migration.__name__}")
                success = migration()
                if not success:
                    logger.error(f"Migration failed: {migration.__name__}")
                    return False
                self.migration_history.append({
                    'name': migration.__name__,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'completed'
                })
            except Exception as e:
                logger.error(f"Migration error in {migration.__name__}: {str(e)}")
                return False
        
        logger.info("All TrustStream Neo4j migrations completed successfully")
        return True
    
    def create_truststream_indexes(self) -> bool:
        """
        Create indexes for TrustStream properties to optimize queries.
        
        Returns:
            bool: True if indexes were created successfully
        """
        try:
            # User trust indexes
            db.cypher_query("CREATE INDEX user_trust_score IF NOT EXISTS FOR (u:Users) ON (u.trust_score)")
            db.cypher_query("CREATE INDEX user_trust_rank IF NOT EXISTS FOR (u:Users) ON (u.trust_rank)")
            db.cypher_query("CREATE INDEX user_moderation_status IF NOT EXISTS FOR (u:Users) ON (u.moderation_status)")
            
            # Post moderation indexes
            db.cypher_query("CREATE INDEX post_moderation_status IF NOT EXISTS FOR (p:Post) ON (p.moderation_status)")
            db.cypher_query("CREATE INDEX post_trust_score IF NOT EXISTS FOR (p:Post) ON (p.content_trust_score)")
            db.cypher_query("CREATE INDEX post_risk_level IF NOT EXISTS FOR (p:Post) ON (p.risk_level)")
            
            # Community health indexes
            db.cypher_query("CREATE INDEX community_health_score IF NOT EXISTS FOR (c:Community) ON (c.community_health_score)")
            db.cypher_query("CREATE INDEX community_safety_rating IF NOT EXISTS FOR (c:Community) ON (c.safety_rating)")
            
            # TrustProfile indexes
            db.cypher_query("CREATE INDEX trust_profile_user_id IF NOT EXISTS FOR (tp:TrustProfile) ON (tp.user_id)")
            db.cypher_query("CREATE INDEX trust_profile_overall_score IF NOT EXISTS FOR (tp:TrustProfile) ON (tp.overall_trust_score)")
            
            # ModerationDecision indexes
            db.cypher_query("CREATE INDEX moderation_decision_timestamp IF NOT EXISTS FOR (md:ModerationDecision) ON (md.timestamp)")
            db.cypher_query("CREATE INDEX moderation_decision_status IF NOT EXISTS FOR (md:ModerationDecision) ON (md.decision)")
            
            logger.info("TrustStream indexes created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating TrustStream indexes: {str(e)}")
            return False
    
    def create_truststream_constraints(self) -> bool:
        """
        Create constraints for TrustStream nodes to ensure data integrity.
        
        Returns:
            bool: True if constraints were created successfully
        """
        try:
            # TrustProfile constraints
            db.cypher_query("CREATE CONSTRAINT trust_profile_user_id IF NOT EXISTS FOR (tp:TrustProfile) REQUIRE tp.user_id IS UNIQUE")
            
            # ModerationDecision constraints
            db.cypher_query("CREATE CONSTRAINT moderation_decision_id IF NOT EXISTS FOR (md:ModerationDecision) REQUIRE md.decision_id IS UNIQUE")
            
            # AgentAnalysis constraints
            db.cypher_query("CREATE CONSTRAINT agent_analysis_id IF NOT EXISTS FOR (aa:AgentAnalysis) REQUIRE aa.analysis_id IS UNIQUE")
            
            # TrustRelationship constraints (ensure no duplicate relationships)
            db.cypher_query("CREATE CONSTRAINT trust_relationship_id IF NOT EXISTS FOR (tr:TrustRelationship) REQUIRE tr.relationship_id IS UNIQUE")
            
            logger.info("TrustStream constraints created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating TrustStream constraints: {str(e)}")
            return False
    
    def create_trust_relationships(self) -> bool:
        """
        Create relationship types for TrustStream network analysis.
        
        Returns:
            bool: True if relationships were created successfully
        """
        try:
            # Note: Neo4j doesn't require explicit relationship type creation
            # This method documents the relationship types used in TrustStream
            
            relationship_types = [
                "HAS_TRUST_PROFILE",
                "HAS_MODERATION_DECISION", 
                "HAS_AGENT_ANALYSIS",
                "TRUSTS",
                "DISTRUSTS",
                "MODERATES",
                "ANALYZED_BY",
                "SIMILAR_TO",
                "INFLUENCES",
                "BELONGS_TO_CLUSTER"
            ]
            
            logger.info(f"TrustStream relationship types documented: {relationship_types}")
            return True
            
        except Exception as e:
            logger.error(f"Error documenting trust relationships: {str(e)}")
            return False
    
    def migrate_existing_user_data(self) -> bool:
        """
        Add TrustStream fields to existing User nodes.
        
        Returns:
            bool: True if migration succeeded
        """
        try:
            # Add trust scoring fields to existing users
            query = """
            MATCH (u:Users)
            WHERE u.trust_score IS NULL
            SET u.trust_score = 2.0,
                u.trust_rank = 'bronze',
                u.trust_percentile = 50.0,
                u.content_quality_score = 2.0,
                u.engagement_authenticity = 2.0,
                u.violation_risk_score = 0.0,
                u.moderation_status = 'active',
                u.violation_count = 0,
                u.warning_count = 0,
                u.trusted_by_count = 0,
                u.trusts_count = 0,
                u.trust_last_updated = datetime()
            RETURN count(u) as updated_users
            """
            
            result, _ = db.cypher_query(query)
            updated_count = result[0][0] if result else 0
            
            logger.info(f"Updated {updated_count} existing users with TrustStream fields")
            return True
            
        except Exception as e:
            logger.error(f"Error migrating existing user data: {str(e)}")
            return False
    
    def migrate_existing_post_data(self) -> bool:
        """
        Add TrustStream moderation fields to existing Post nodes.
        
        Returns:
            bool: True if migration succeeded
        """
        try:
            # Add moderation fields to existing posts
            query = """
            MATCH (p:Post)
            WHERE p.moderation_status IS NULL
            SET p.content_trust_score = 2.0,
                p.authenticity_score = 2.0,
                p.safety_score = 2.0,
                p.moderation_status = 'approved',
                p.moderation_confidence = 0.8,
                p.human_reviewed = false,
                p.violation_types = [],
                p.violation_severity = 0.0,
                p.risk_level = 'low',
                p.user_appealed = false,
                p.engagement_quality = 2.0,
                p.viral_potential = 0.0,
                p.trust_last_updated = datetime()
            RETURN count(p) as updated_posts
            """
            
            result, _ = db.cypher_query(query)
            updated_count = result[0][0] if result else 0
            
            logger.info(f"Updated {updated_count} existing posts with TrustStream fields")
            return True
            
        except Exception as e:
            logger.error(f"Error migrating existing post data: {str(e)}")
            return False
    
    def migrate_existing_community_data(self) -> bool:
        """
        Add TrustStream health monitoring fields to existing Community nodes.
        
        Returns:
            bool: True if migration succeeded
        """
        try:
            # Add health monitoring fields to existing communities
            query = """
            MATCH (c:Community)
            WHERE c.community_health_score IS NULL
            SET c.community_health_score = 2.0,
                c.content_quality_avg = 2.0,
                c.member_trust_avg = 2.0,
                c.engagement_authenticity = 2.0,
                c.auto_moderation_enabled = true,
                c.moderation_strictness = 'medium',
                c.trust_threshold = 1.0,
                c.violation_rate = 0.0,
                c.toxicity_score = 0.0,
                c.safety_rating = 'safe',
                c.trust_based_permissions = false,
                c.high_trust_benefits = false,
                c.trust_verification_required = false,
                c.total_moderations = 0,
                c.auto_approvals = 0,
                c.human_reviews = 0,
                c.growth_rate = 0.0,
                c.retention_rate = 0.0,
                c.activity_score = 2.0,
                c.health_last_updated = datetime()
            RETURN count(c) as updated_communities
            """
            
            result, _ = db.cypher_query(query)
            updated_count = result[0][0] if result else 0
            
            logger.info(f"Updated {updated_count} existing communities with TrustStream fields")
            return True
            
        except Exception as e:
            logger.error(f"Error migrating existing community data: {str(e)}")
            return False
    
    def create_trust_profiles(self) -> bool:
        """
        Create TrustProfile nodes for all existing users.
        
        Returns:
            bool: True if trust profiles were created successfully
        """
        try:
            # Create TrustProfile nodes for users who don't have them
            query = """
            MATCH (u:Users)
            WHERE NOT EXISTS((u)-[:HAS_TRUST_PROFILE]->(:TrustProfile))
            CREATE (tp:TrustProfile {
                user_id: u.user_id,
                iq_score: 2.0,
                appeal_score: 2.0,
                social_score: 2.0,
                humanity_score: 2.0,
                overall_trust_score: 2.0,
                trust_rank: 'bronze',
                trust_percentile: 50.0,
                behavioral_consistency: 2.0,
                content_authenticity: 2.0,
                community_contribution: 2.0,
                violation_history: [],
                positive_interactions: 0,
                negative_interactions: 0,
                peer_endorsements: 0,
                expert_validations: 0,
                created_at: datetime(),
                last_updated: datetime()
            })
            CREATE (u)-[:HAS_TRUST_PROFILE]->(tp)
            RETURN count(tp) as created_profiles
            """
            
            result, _ = db.cypher_query(query)
            created_count = result[0][0] if result else 0
            
            logger.info(f"Created {created_count} TrustProfile nodes")
            return True
            
        except Exception as e:
            logger.error(f"Error creating trust profiles: {str(e)}")
            return False
    
    def initialize_trust_network(self) -> bool:
        """
        Initialize trust network relationships based on existing interactions.
        
        Returns:
            bool: True if trust network was initialized successfully
        """
        try:
            # Create initial trust relationships based on positive interactions
            # Users who frequently interact positively should have trust relationships
            
            query = """
            MATCH (u1:Users)-[:LIKED]->(p:Post)<-[:POSTED]-(u2:Users)
            WHERE u1 <> u2
            WITH u1, u2, count(*) as interactions
            WHERE interactions >= 5
            MERGE (u1)-[tr:TRUSTS]->(u2)
            ON CREATE SET tr.strength = 0.3,
                         tr.created_at = datetime(),
                         tr.interaction_count = interactions,
                         tr.trust_type = 'engagement_based'
            RETURN count(tr) as trust_relationships_created
            """
            
            result, _ = db.cypher_query(query)
            trust_count = result[0][0] if result else 0
            
            # Create community-based trust relationships
            community_trust_query = """
            MATCH (u1:Users)-[:MEMBER_OF]->(c:Community)<-[:MEMBER_OF]-(u2:Users)
            WHERE u1 <> u2
            WITH u1, u2, collect(c) as shared_communities
            WHERE size(shared_communities) >= 2
            MERGE (u1)-[tr:TRUSTS]->(u2)
            ON CREATE SET tr.strength = 0.2,
                         tr.created_at = datetime(),
                         tr.shared_communities = size(shared_communities),
                         tr.trust_type = 'community_based'
            RETURN count(tr) as community_trust_relationships
            """
            
            result2, _ = db.cypher_query(community_trust_query)
            community_trust_count = result2[0][0] if result2 else 0
            
            logger.info(f"Created {trust_count} engagement-based and {community_trust_count} community-based trust relationships")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing trust network: {str(e)}")
            return False
    
    def validate_migration(self) -> Dict[str, Any]:
        """
        Validate that all TrustStream migrations were applied correctly.
        
        Returns:
            dict: Validation results with counts and status
        """
        validation_results = {}
        
        try:
            # Check user trust fields
            user_query = "MATCH (u:Users) WHERE u.trust_score IS NOT NULL RETURN count(u) as users_with_trust"
            result, _ = db.cypher_query(user_query)
            validation_results['users_with_trust_fields'] = result[0][0] if result else 0
            
            # Check trust profiles
            profile_query = "MATCH (tp:TrustProfile) RETURN count(tp) as trust_profiles"
            result, _ = db.cypher_query(profile_query)
            validation_results['trust_profiles_created'] = result[0][0] if result else 0
            
            # Check post moderation fields
            post_query = "MATCH (p:Post) WHERE p.moderation_status IS NOT NULL RETURN count(p) as posts_with_moderation"
            result, _ = db.cypher_query(post_query)
            validation_results['posts_with_moderation_fields'] = result[0][0] if result else 0
            
            # Check community health fields
            community_query = "MATCH (c:Community) WHERE c.community_health_score IS NOT NULL RETURN count(c) as communities_with_health"
            result, _ = db.cypher_query(community_query)
            validation_results['communities_with_health_fields'] = result[0][0] if result else 0
            
            # Check trust relationships
            trust_rel_query = "MATCH ()-[tr:TRUSTS]->() RETURN count(tr) as trust_relationships"
            result, _ = db.cypher_query(trust_rel_query)
            validation_results['trust_relationships'] = result[0][0] if result else 0
            
            # Check indexes
            index_query = "SHOW INDEXES YIELD name WHERE name CONTAINS 'trust' RETURN count(*) as trust_indexes"
            result, _ = db.cypher_query(index_query)
            validation_results['trust_indexes'] = result[0][0] if result else 0
            
            validation_results['migration_status'] = 'completed'
            validation_results['validation_timestamp'] = datetime.now().isoformat()
            
        except Exception as e:
            validation_results['error'] = str(e)
            validation_results['migration_status'] = 'validation_failed'
        
        return validation_results
    
    def rollback_migration(self, migration_name: str) -> bool:
        """
        Rollback a specific TrustStream migration.
        
        Args:
            migration_name: Name of the migration to rollback
            
        Returns:
            bool: True if rollback succeeded
        """
        rollback_queries = {
            'migrate_existing_user_data': [
                "MATCH (u:Users) REMOVE u.trust_score, u.trust_rank, u.trust_percentile, u.content_quality_score, u.engagement_authenticity, u.violation_risk_score, u.moderation_status, u.violation_count, u.warning_count, u.trusted_by_count, u.trusts_count, u.trust_last_updated"
            ],
            'migrate_existing_post_data': [
                "MATCH (p:Post) REMOVE p.content_trust_score, p.authenticity_score, p.safety_score, p.moderation_status, p.moderation_confidence, p.human_reviewed, p.violation_types, p.violation_severity, p.risk_level, p.user_appealed, p.engagement_quality, p.viral_potential, p.trust_last_updated"
            ],
            'migrate_existing_community_data': [
                "MATCH (c:Community) REMOVE c.community_health_score, c.content_quality_avg, c.member_trust_avg, c.engagement_authenticity, c.auto_moderation_enabled, c.moderation_strictness, c.trust_threshold, c.violation_rate, c.toxicity_score, c.safety_rating, c.trust_based_permissions, c.high_trust_benefits, c.trust_verification_required, c.total_moderations, c.auto_approvals, c.human_reviews, c.growth_rate, c.retention_rate, c.activity_score, c.health_last_updated"
            ],
            'create_trust_profiles': [
                "MATCH (u:Users)-[r:HAS_TRUST_PROFILE]->(tp:TrustProfile) DELETE r, tp"
            ],
            'initialize_trust_network': [
                "MATCH ()-[tr:TRUSTS]->() DELETE tr"
            ]
        }
        
        try:
            if migration_name in rollback_queries:
                for query in rollback_queries[migration_name]:
                    db.cypher_query(query)
                logger.info(f"Rolled back migration: {migration_name}")
                return True
            else:
                logger.error(f"No rollback available for migration: {migration_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error rolling back migration {migration_name}: {str(e)}")
            return False


def run_truststream_neo4j_migrations():
    """
    Main function to run all TrustStream Neo4j migrations.
    
    Returns:
        bool: True if all migrations succeeded
    """
    manager = Neo4jMigrationManager()
    return manager.run_all_migrations()


def validate_truststream_neo4j_setup():
    """
    Validate that TrustStream Neo4j setup is correct.
    
    Returns:
        dict: Validation results
    """
    manager = Neo4jMigrationManager()
    return manager.validate_migration()


if __name__ == "__main__":
    # Run migrations when script is executed directly
    success = run_truststream_neo4j_migrations()
    if success:
        print("TrustStream Neo4j migrations completed successfully")
        validation = validate_truststream_neo4j_setup()
        print("Validation results:", json.dumps(validation, indent=2))
    else:
        print("TrustStream Neo4j migrations failed")