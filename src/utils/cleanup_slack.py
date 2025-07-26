#!/usr/bin/env python3
"""
Slack Channel Cleanup Utility

This script cleans up Slack channels created during LazyPreneur testing.
"""

import os
import sys
import logging
from typing import List, Dict, Optional

# Add the parent directory to the path so we can import our tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.slack import Slack, SlackBotManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Channels that were likely created during testing
TEST_CHANNELS = [
    "startup-team",
    "executive-decisions", 
    "financial-planning",
    "technical-strategy",
    "marketing-strategy",
    "lazypreneur-test",
    "test-channel",
    "demo-channel"
]

class SlackCleanup:
    """Utility to clean up Slack channels created during testing"""
    
    def __init__(self):
        """Initialize the cleanup utility"""
        self.slack_manager = SlackBotManager()
        self.ceo_bot = None
        self._setup_ceo_bot()
    
    def _setup_ceo_bot(self):
        """Setup CEO bot for cleanup"""
        token = os.getenv('SLACK_API_TOKEN_CEO')
        
        if token:
            try:
                self.ceo_bot = self.slack_manager.add_bot("CEO", token)
                logger.info("Added CEO bot for cleanup")
            except Exception as e:
                logger.warning(f"Failed to add CEO bot: {e}")
        else:
            logger.warning("CEO Slack token not found (SLACK_API_TOKEN_CEO)")
    
    def list_channels(self) -> List[str]:
        """List all channels the CEO bot can see"""
        if not self.ceo_bot:
            logger.error("CEO bot not available")
            return []
        
        try:
            result = self.ceo_bot.list_all_channels()
            if result["success"]:
                channels = result.get("channels", [])
                channel_names = [ch.get("name", "") for ch in channels]
                logger.info(f"CEO bot can see {len(channel_names)} channels")
                return channel_names
            else:
                logger.warning(f"Failed to list channels: {result.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Error listing channels: {e}")
            return []
    
    def find_test_channels(self) -> List[str]:
        """Find test channels that need cleanup"""
        all_channels = self.list_channels()
        test_channels_found = []
        
        for channel in all_channels:
            if any(test_channel in channel.lower() for test_channel in TEST_CHANNELS):
                test_channels_found.append(channel)
        
        if test_channels_found:
            logger.info(f"Found test channels: {test_channels_found}")
        
        return test_channels_found
    
    def archive_channel(self, channel_name: str) -> bool:
        """Archive a specific channel"""
        if not self.ceo_bot:
            logger.error("CEO bot not available")
            return False
        
        try:
            # First, try to join the channel if we're not already in it
            join_result = self.ceo_bot.join_channel(channel_name)
            if not join_result["success"]:
                logger.warning(f"Could not join channel {channel_name}: {join_result.get('error')}")
            
            # Archive the channel
            archive_result = self.ceo_bot.archive_channel(channel_name)
            if archive_result["success"]:
                logger.info(f"Successfully archived channel: {channel_name}")
                return True
            else:
                logger.error(f"Failed to archive channel {channel_name}: {archive_result.get('error')}")
                return False
            
        except Exception as e:
            logger.error(f"Error archiving channel {channel_name}: {e}")
            return False
    
    def cleanup_test_channels(self, dry_run: bool = True) -> List[str]:
        """Clean up test channels"""
        test_channels = self.find_test_channels()
        cleaned_channels = []
        
        if not test_channels:
            logger.info("No test channels found to clean up")
            return cleaned_channels
        
        logger.info(f"Found test channels to clean up: {test_channels}")
        
        if dry_run:
            logger.info("DRY RUN MODE - No channels will actually be archived")
        
        for channel in test_channels:
            if dry_run:
                logger.info(f"[DRY RUN] Would archive channel: {channel}")
                cleaned_channels.append(channel)
            else:
                if self.archive_channel(channel):
                    cleaned_channels.append(channel)
                    logger.info(f"Successfully archived channel: {channel}")
                else:
                    logger.error(f"Failed to archive channel: {channel}")
        
        return cleaned_channels
    
    def show_cleanup_summary(self):
        """Show a summary of what would be cleaned up"""
        logger.info("=== SLACK CHANNEL CLEANUP SUMMARY ===")
        
        # List all channels
        all_channels = self.list_channels()
        logger.info(f"CEO bot can see {len(all_channels)} channels")
        for channel in all_channels:
            logger.info(f"  - {channel}")
        
        # Find test channels
        test_channels = self.find_test_channels()
        if test_channels:
            logger.info(f"\nTest channels found: {len(test_channels)} channels")
            logger.info(f"Test channels: {test_channels}")
        else:
            logger.info("\nNo test channels found")
        
        logger.info("=== END SUMMARY ===")

def main():
    """Main cleanup function"""
    print("🚀 Slack Channel Cleanup Utility")
    print("=" * 40)
    
    # Check if we have the CEO Slack token
    if not os.getenv('SLACK_API_TOKEN_CEO'):
        print("❌ CEO Slack token not found!")
        print("Please set the following environment variable:")
        print("  - SLACK_API_TOKEN_CEO")
        return
    
    print("✅ Found CEO Slack token")
    
    # Initialize cleanup utility
    cleanup = SlackCleanup()
    
    if not cleanup.ceo_bot:
        print("❌ CEO bot could not be initialized!")
        return
    
    print("✅ Initialized CEO bot")
    
    # Show summary
    cleanup.show_cleanup_summary()
    
    # Ask user what to do
    print("\nWhat would you like to do?")
    print("1. Dry run (show what would be cleaned up)")
    print("2. Actually clean up test channels")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        print("\n🔍 Running dry run...")
        cleaned = cleanup.cleanup_test_channels(dry_run=True)
        if cleaned:
            print(f"✅ Would clean up {len(cleaned)} channels")
        else:
            print("✅ No channels to clean up")
    
    elif choice == "2":
        print("\n⚠️  WARNING: This will actually archive channels!")
        confirm = input("Are you sure? Type 'yes' to continue: ").strip().lower()
        
        if confirm == "yes":
            print("\n🧹 Cleaning up test channels...")
            cleaned = cleanup.cleanup_test_channels(dry_run=False)
            if cleaned:
                print(f"✅ Cleaned up {len(cleaned)} channels")
            else:
                print("✅ No channels were cleaned up")
        else:
            print("❌ Cleanup cancelled")
    
    else:
        print("👋 Exiting without cleanup")

if __name__ == "__main__":
    main()
