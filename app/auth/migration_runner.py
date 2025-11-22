"""
Data Migration Runner
Handles the migration of existing data to support user-based isolation.
"""

import logging
import streamlit as st
from typing import Dict, Any
from .data_migration import DataMigration
from .user_management import UserManager
from ..database import QDRANT_CLIENT

logger = logging.getLogger(__name__)

class MigrationRunner:
    """Runs data migration and user setup."""
    
    def __init__(self):
        self.qdrant_client = QDRANT_CLIENT
        self.user_manager = UserManager(self.qdrant_client)  # type: ignore[arg-type]
        self.data_migration = DataMigration(self.qdrant_client)  # type: ignore[arg-type]
    
    def run_full_migration(self) -> Dict[str, Any]:
        """Run the complete migration process."""
        results = {
            "users_created": 0,
            "data_migrated": {},
            "verification": {},
            "success": True,
            "errors": []
        }
        
        try:
            # Step 1: Ensure users collection and default user
            logger.info("Step 1: Setting up users collection...")
            try:
                # This will create the users collection and default user
                self.user_manager._ensure_users_collection()
                results["users_created"] = 1
                logger.info("Users collection setup complete")
            except Exception as e:
                error_msg = f"Error setting up users collection: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                results["success"] = False
            
            # Step 2: Migrate existing data
            logger.info("Step 2: Migrating existing data...")
            try:
                migration_results = self.data_migration.migrate_all_data()
                results["data_migrated"] = migration_results
                logger.info(f"Data migration complete: {migration_results}")
            except Exception as e:
                error_msg = f"Error migrating data: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                results["success"] = False
            
            # Step 3: Verify migration
            logger.info("Step 3: Verifying migration...")
            try:
                verification_results = self.data_migration.verify_migration()
                results["verification"] = verification_results
                logger.info(f"Migration verification complete: {verification_results}")
            except Exception as e:
                error_msg = f"Error verifying migration: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                results["success"] = False
            
            return results
            
        except Exception as e:
            error_msg = f"Unexpected error during migration: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            results["success"] = False
            return results
    
    def check_migration_status(self) -> Dict[str, Any]:
        """Check the current migration status."""
        try:
            # Check if users collection exists
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            users_exist = "users" in collection_names
            
            # Check if default user exists
            default_user = None
            if users_exist:
                default_user = self.user_manager.get_user_by_username("default_user")
            
            # Check data migration status
            verification_results = self.data_migration.verify_migration()
            
            return {
                "users_collection_exists": users_exist,
                "default_user_exists": default_user is not None,
                "data_migration_status": verification_results,
                "migration_complete": all(
                    status.get("migration_complete", False) 
                    for status in verification_results.values() 
                    if isinstance(status, dict)
                )
            }
            
        except Exception as e:
            logger.error(f"Error checking migration status: {e}")
            return {
                "error": str(e),
                "users_collection_exists": False,
                "default_user_exists": False,
                "data_migration_status": {},
                "migration_complete": False
            }

def run_migration_ui():
    """Run migration with Streamlit UI."""
    st.markdown("# 🔄 Data Migration")
    st.markdown("This will migrate existing data to support user-based isolation.")
    
    migration_runner = MigrationRunner()
    
    # Check current status
    st.markdown("## 📊 Current Status")
    status = migration_runner.check_migration_status()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Users Collection", 
            "✅ Exists" if status["users_collection_exists"] else "❌ Missing"
        )
    
    with col2:
        st.metric(
            "Default User", 
            "✅ Exists" if status["default_user_exists"] else "❌ Missing"
        )
    
    with col3:
        st.metric(
            "Migration Complete", 
            "✅ Complete" if status["migration_complete"] else "❌ Incomplete"
        )
    
    with col4:
        if status.get("error"):
            st.metric("Status", "❌ Error")
        else:
            st.metric("Status", "✅ Ready")
    
    # Show detailed status
    if status.get("data_migration_status"):
        st.markdown("### 📋 Migration Details")
        for collection, details in status["data_migration_status"].items():
            if isinstance(details, dict):
                st.markdown(f"**{collection}:**")
                st.markdown(f"- Total: {details.get('total', 0)}")
                st.markdown(f"- With user_id: {details.get('with_user_id', 0)}")
                st.markdown(f"- Without user_id: {details.get('without_user_id', 0)}")
                st.markdown(f"- Status: {'✅ Complete' if details.get('migration_complete') else '❌ Incomplete'}")
            else:
                st.markdown(f"**{collection}:** {details}")
    
    # Migration button
    st.markdown("## 🚀 Run Migration")
    
    if st.button("Start Migration", type="primary"):
        with st.spinner("Running migration..."):
            results = migration_runner.run_full_migration()
        
        if results["success"]:
            st.success("✅ Migration completed successfully!")
            
            # Show results
            st.markdown("### 📈 Migration Results")
            
            if results["data_migrated"]:
                st.markdown("**Data Migrated:**")
                for collection, count in results["data_migrated"].items():
                    st.markdown(f"- {collection}: {count} items")
            
            if results["verification"]:
                st.markdown("**Verification Results:**")
                for collection, details in results["verification"].items():
                    if isinstance(details, dict):
                        st.markdown(f"- {collection}: {'✅ Complete' if details.get('migration_complete') else '❌ Incomplete'}")
            
            st.info("🔄 Please refresh the page to see the updated status.")
            
        else:
            st.error("❌ Migration failed!")
            
            if results["errors"]:
                st.markdown("**Errors:**")
                for error in results["errors"]:
                    st.error(f"- {error}")
    
    # Rollback option (use with caution)
    st.markdown("## ⚠️ Rollback Migration")
    st.warning("⚠️ This will remove user_id fields from all data. Use only if migration failed.")
    
    if st.button("Rollback Migration", type="secondary"):
        with st.spinner("Rolling back migration..."):
            success = migration_runner.data_migration.rollback_migration()
        
        if success:
            st.success("✅ Rollback completed successfully!")
            st.info("🔄 Please refresh the page to see the updated status.")
        else:
            st.error("❌ Rollback failed!")
    
    # Help information
    st.markdown("---")
    st.markdown("### 💡 Migration Information")
    st.markdown("""
    **What this migration does:**
    - Creates a users collection in the database
    - Creates a default user account (username: `default_user`, password: `default`)
    - Adds `user_id` field to all existing data
    - Assigns all existing data to the default user
    
    **After migration:**
    - You can log in with the default account
    - All existing data will be available to the default user
    - New users will have their own isolated data
    - Each user can create their own value components and personas
    """) 