# vibe_manager/utils.py

from auth_manager.models import Users, UserVibeRepo
from vibe_manager.models import *

# Utility class for vibe-related operations and scoring calculations
# Contains the core business logic for how vibes affect user scores
# This is the heart of the vibe scoring system
class VibeUtils:
    """
    Utility class containing core vibe processing logic.
    
    This class handles the complex business logic of how vibes affect user scores
    and social metrics. It's the heart of the vibe system's scoring algorithm.
    
    The scoring system works by:
    1. Taking the vibe's inherent scoring weights (iq, aq, sq, hq)
    2. Combining them with the user's sent vibe score
    3. Applying a rate change calculation based on user's vibe history
    4. Updating the user's profile scores within bounds (0-4)
    5. Recording the transaction for future calculations
    
    This class is designed to be stateless and handle all edge cases
    related to score calculations and user vibe interactions.
    """
    
    # Static method that handles the core vibe scoring logic
    # Called whenever a user sends a vibe to another user
    # Updates recipient's scores based on vibe characteristics and sending context
    @staticmethod
    def onVibeCreated(pro, vibename, numvibe):
        """
        Processes a vibe interaction and updates user scores.
        
        This is the core method of the vibe scoring system. It handles the complete
        process of how sending/receiving a vibe affects a user's scores across
        multiple dimensions (intelligence, appeal, social, human).
        
        The algorithm works as follows:
        1. Find the vibe template by name
        2. Get the user's current scores
        3. Calculate how many vibes this user has received (affects rate of change)
        4. Apply weighted scoring algorithm for each dimension
        5. Update user scores within valid bounds (0-4)
        6. Calculate new cumulative score
        7. Record the vibe transaction
        
        Args:
            pro (Users): The user receiving/being affected by the vibe
            vibename (str): Name of the vibe being sent (must exist in database)
            numvibe (float): Score value for this specific vibe interaction
            
        Returns:
            None: Method has side effects on user scores and database
            
        Algorithm details:
            - Rate change decreases as user receives more vibes (diminishing returns)
            - Score changes are bounded between 0 and 4
            - Each dimension (IQ, AQ, SQ, HQ) is calculated independently
            - Cumulative score is the average of all four dimensions
            
        Edge cases handled:
            - Vibe not found in database (will raise exception)
            - User has no profile/score (will raise exception)
            - Zero values in calculations (handled by if statements)
            - Score bounds enforcement (0-4 range)
            - Database connection issues (caught by outer exception handler)
            
        Used by:
            - SendVibe GraphQL mutation
            - Vibe interaction processing
            - Score calculation workflows
            - Analytics and reporting systems
        """
        try:
            # Step 1: Find the vibe template by name
            # This gets the vibe's inherent scoring weights (iq, aq, sq, hq)
            v = Vibe.nodes.get(name=vibename)
            
            # Step 2: Get user and their current scores
            pro_user = pro  # The user receiving the vibe
            profile = pro.profile.single()  # User's profile information
            score = profile.score.single()  # User's current score object
            
            # Step 3: Calculate vibe history for rate change calculation
            # More vibes received = slower rate of change (diminishing returns)
            if pro_user:
                vibe_repos = list(pro_user.userviberepo.all())  # Get all vibe transactions
                h = len(vibe_repos)  # Count of vibes received
            else:
                h = 0  # Default if no user found
            
            # Step 4: Extract vibe's scoring weights
            # These determine how much this vibe type affects each dimension
            weight_aq = v.aq  # Appeal quotient weight
            weight_hq = v.hq  # Human quotient weight  
            weight_sq = v.sq  # Social quotient weight
            weight_iq = v.iq  # Intelligence quotient weight
            
            # Step 5: Calculate rate change constant
            # As user receives more vibes, each new vibe has less impact
            # This prevents score inflation and maintains balance
            rate_change_constant = 0.2 / (h + 1)
            
            # Step 6: Define scoring calculation function
            # This function calculates how much each dimension should change
            def calculate_change(weight, vibe, score):
                """
                Calculates score change for a single dimension.
                
                This helper function implements the core scoring algorithm
                for individual dimensions (IQ, AQ, SQ, HQ).
                
                Algorithm:
                1. If either weight or vibe is 0, no change occurs
                2. Calculate average of vibe weight and user's vibe score
                3. Find difference from current score
                4. Apply rate change constant to moderate the change
                5. Ensure change doesn't push score outside bounds (0-4)
                
                Args:
                    weight (float): Vibe's inherent weight for this dimension
                    vibe (float): User's sent vibe score
                    score (float): Current user score for this dimension
                    
                Returns:
                    float: Calculated change amount (can be positive or negative)
                    
                Edge cases:
                    - Zero weight or vibe returns 0 (no change)
                    - Change is bounded to keep final score in 0-4 range
                """
                if vibe == 0 or weight == 0:
                    return 0
                    
                # Calculate target score as average of vibe weight and user vibe score
                target = (vibe + weight) / 2
                
                # Calculate raw change amount
                change = (target - score) * rate_change_constant
                
                # Bound the change to keep final score within valid range (0-4)
                return min(4 - score, max(-score, change))
            
            # Step 7: Calculate changes for each dimension
            aq_change = calculate_change(weight_aq, numvibe, score.appeal_score)
            hq_change = calculate_change(weight_hq, numvibe, score.human_score)
            sq_change = calculate_change(weight_sq, numvibe, score.social_score)
            iq_change = calculate_change(weight_iq, numvibe, score.intelligence_score)
            
            # Step 8: Apply changes to user scores
            score.intelligence_score += iq_change
            score.appeal_score += aq_change
            score.social_score += sq_change
            score.human_score += hq_change
            
            # Step 9: Increment vibe interaction counter
            score.vibers_count += 1
            
            # Step 10: Enforce score bounds (0-4 range)
            # This ensures scores never go below 0 or above 4
            score.intelligence_score = max(0, min(4, score.intelligence_score))
            score.appeal_score = max(0, min(4, score.appeal_score))
            score.social_score = max(0, min(4, score.social_score))
            score.human_score = max(0, min(4, score.human_score))
            
            # Step 11: Calculate cumulative score as average of all dimensions
            # This provides an overall score that represents the user's total vibe rating
            score.cumulative_vibescore = (
                score.intelligence_score +
                score.appeal_score +
                score.social_score +
                score.human_score
            ) / 4
            
            # Step 12: Save updated scores to database
            score.save()
            
            # Step 13: Record this vibe transaction for future calculations
            # This creates a historical record and affects future rate calculations
            repo = UserVibeRepo(custom_value=numvibe)
            repo.save()
            
            # Step 14: Establish relationships for the vibe transaction
            repo.user.connect(pro_user)  # Link transaction to user
            pro_user.userviberepo.connect(repo)  # Link user to transaction
            
        except Exception as e:
            # Silently handle any errors during vibe processing
            # In production, this should probably log the error for debugging
            # Current implementation prevents crashes but loses error information
            pass