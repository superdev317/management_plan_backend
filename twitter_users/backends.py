
from accounts.models import (
    User,UserProfile,
)
from twitter_users import settings

class TwitterBackend(object):
    def authenticate(self, twitter_id=None, username=None, token=None, secret=None):
        # find or create the user
        #email    = "%s@twitter.com" % username
        
        try:            
            if(UserProfile.objects.filter(twitter_id=twitter_id).exists()):
               # email    = "%s@twitter.com" % username
                info = UserProfile.objects.get(twitter_id=twitter_id)
                user = User.objects.get(id=info.user_id)
                return user

            elif(User.objects.filter(user_name=username).exists()):
                user  = User.objects.get(user_name=username)

                profile = UserProfile.objects.get(user_id=user.id)
                if profile.twitter_id is None:
                    UserProfile.objects.filter(user_id=user.id).update(twitter_id=twitter_id)
                    UserProfile.objects.filter(user_id=user.id).update(secret=secret)
                    UserProfile.objects.filter(user_id=user.id).update(token=token)
                    return user                                                                                                                                                                                                                                             
            else:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           
                user = User.objects.create_user(user_name=username) 
                                            
                user.save()
                info = User.objects.get(user_name=username)
                UserProfile.objects.filter(user_id=info.id).update(twitter_id=twitter_id)
                UserProfile.objects.filter(user_id=info.id).update(secret=secret)
                UserProfile.objects.filter(user_id=info.id).update(token=token)

                return user

        except UserProfile.DoesNotExist:
            pass
        

            
    
    # def get_user(self, user_id):
    #     try:
    #         return User.objects.get(pk=user_id)
    #     except User.DoesNotExist:
    #         return None
