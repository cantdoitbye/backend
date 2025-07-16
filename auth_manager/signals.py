from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Users,Profile,OnboardingStatus,Score
from .models import ConnectionStats

from msg.utils import register_user_on_matrix
from msg.models import MatrixProfile

import asyncio

@receiver(post_save, sender=User)
def create_or_update_user_meta_data(sender, instance, created, **kwargs):
    if created:
        # Create a new Users node in Neo4j
        user_node=Users(user_id=instance.id,password=instance.password,email=instance.email)
        user_node.save()

        profile=Profile(user_id=instance.id).save()
        profile.save() 

        onboarding_status = OnboardingStatus(email_verified=False)
        onboarding_status.save()

        profile.user.connect(user_node)
        user_node.profile.connect(profile)
        onboarding_status.profile.connect(profile)
        profile.onboarding.connect(onboarding_status)

        user_score=Score()
        user_score.save()
        profile.score.connect(user_score)

        user_circle=ConnectionStats()
        user_circle.save()
        user_node.connection_stat.connect(user_circle)
        instance.username=user_node.uid
        instance.save()


        # Register the user on Matrix
        try:
            #Note:Password logic Will changed.
            matrix_user= asyncio.run(register_user_on_matrix(username=instance.username, password=instance.username))
            pending_matrix_registration = matrix_user[1] is None
            matrix_access_token=matrix_user[0]
            matrix_user_id=matrix_user[1]

        except Exception as e:
            # should be logged by logger
            # print(f"Matrix registration failed for user {instance.email}: {e}")
            matrix_user_id = None
            pending_matrix_registration = True
            matrix_access_token=None

        # Save Matrix profile to track registration status
        MatrixProfile.objects.create(
            user=instance,
            matrix_user_id=matrix_user_id,
            pending_matrix_registration=pending_matrix_registration,
            access_token = matrix_access_token
        )




        
    else:
        try:
            # Update existing Users node in Neo4
            user_meta = Users.nodes.get(user_id=str(instance.id))
            user_meta.password=instance.password
            user_meta.email=instance.email
            user_meta.first_name=instance.first_name
            user_meta.last_name=instance.last_name
            user_meta.save()
        except Exception as e:
            # Create a new Users node (Not Found Case)
            Users(user_id=instance.id,email=instance.email).save()
