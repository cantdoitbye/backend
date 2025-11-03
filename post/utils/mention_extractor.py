import re
from typing import List, Set
from auth_manager.models import Users
import logging

logger = logging.getLogger(__name__)

class MentionExtractor:
    """
    Utility class for extracting usernames from text content and converting them to user UIDs.
    
    This provides a centralized way to handle mentions across all content types (posts, 
    comments, stories, bios, etc.) by parsing @username patterns from text and converting
    them to user UIDs for database storage.
    
    Industry standard approach: Extract mentions from actual content rather than relying
    on frontend to send mention lists.
    """
    
    # Regex pattern to match @username mentions
    # Matches @ followed by alphanumeric characters, underscores, and hyphens
    MENTION_PATTERN = re.compile(r'@([a-zA-Z0-9_-]+)')
    
    @staticmethod
    def extract_usernames_from_text(text: str) -> Set[str]:
        """
        Extract all unique usernames from text that are prefixed with @
        
        Args:
            text: The text content to parse (bio, comment, post, etc.)
            
        Returns:
            Set of unique usernames (without @ symbol)
            
        Example:
            extract_usernames_from_text("Hey @john and @jane, check this out! @john again.")
            Returns: {'john', 'jane'}
        """
        if not text:
            return set()
            
        try:
            # Find all matches and extract usernames
            matches = MentionExtractor.MENTION_PATTERN.findall(text)
            
            # Return unique usernames (case-sensitive)
            unique_usernames = set(matches)
            
            print(f"🔍 MENTION EXTRACTOR DEBUG: Extracted usernames from text: {unique_usernames}")
            return unique_usernames
            
        except Exception as e:
            logger.error(f"Error extracting usernames from text: {str(e)}")
            return set()
    
    @staticmethod
    def convert_usernames_to_uids(usernames: Set[str]) -> List[str]:
        """
        Convert usernames to user UIDs by querying the database
        
        Args:
            usernames: Set of usernames to convert
            
        Returns:
            List of user UIDs for valid usernames
        """
        if not usernames:
            return []
            
        user_uids = []
        
        try:
            for username in usernames:
                try:
                    # Query Neo4j for user with this username
                    user = Users.nodes.get(username=username)
                    if user:
                        user_uids.append(user.uid)
                        print(f"🔍 MENTION EXTRACTOR DEBUG: Found UID {user.uid} for username @{username}")
                    else:
                        print(f"🔍 MENTION EXTRACTOR DEBUG: Username @{username} not found in database")
                        
                except Users.DoesNotExist:
                    print(f"🔍 MENTION EXTRACTOR DEBUG: Username @{username} does not exist")
                    continue
                except Exception as e:
                    logger.error(f"Error looking up username @{username}: {str(e)}")
                    continue
                    
            print(f"🔍 MENTION EXTRACTOR DEBUG: Converted usernames to UIDs: {user_uids}")
            return user_uids
            
        except Exception as e:
            logger.error(f"Error converting usernames to UIDs: {str(e)}")
            return []
    
    @staticmethod
    def extract_and_convert_mentions(text: str) -> List[str]:
        """
        Combined method: Extract usernames from text and convert to UIDs
        
        Args:
            text: The text content to parse
            
        Returns:
            List of user UIDs for mentioned users
        """
        usernames = MentionExtractor.extract_usernames_from_text(text)
        return MentionExtractor.convert_usernames_to_uids(usernames)
    
    @staticmethod
    def remove_mentions_from_text(text: str, replace_with: str = "") -> str:
        """
        Remove @username patterns from text (useful for display purposes)
        
        Args:
            text: The text to clean
            replace_with: What to replace the mention with (default empty string)
            
        Returns:
            Text with mentions removed
        """
        if not text:
            return text
            
        try:
            cleaned_text = MentionExtractor.MENTION_PATTERN.sub(replace_with, text)
            # Clean up extra spaces that might be left
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
            return cleaned_text
        except Exception as e:
            logger.error(f"Error removing mentions from text: {str(e)}")
            return text
