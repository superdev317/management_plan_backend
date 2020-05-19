from accounts.models import (
    User,UserProfile,
)
from paypal_users import settings
import string

class PaypalBackend(object):
    def authenticate(self, paypal_id=None,username=None,email=None,birthdate=None):
        # find or create the user
        #paypalid = str.replace(paypal_id, 'https://www.paypal.com/webapps/auth/identity/user/', '')
        paypalid =  paypal_id.split('/')[::-1][0]

        if username:
            name = username.split(' ')
            fname = name[0]
            lname = name[1]


        try:            
            if(UserProfile.objects.filter(paypal_id=paypalid).exists()):
                info = UserProfile.objects.get(paypal_id=paypalid)
                user = User.objects.get(id=info.user_id)
                return user

            elif(User.objects.filter(email=email).exists()):
                user  = User.objects.get(email=email)

                profile = UserProfile.objects.get(user_id=user.id)
                if profile.paypal_id is None:
                    UserProfile.objects.filter(user_id=user.id).update(paypal_id=paypalid)
                    UserProfile.objects.filter(user_id=user.id).update(first_name=fname)
                    UserProfile.objects.filter(user_id=user.id).update(last_name=lname)

                    return user                                                                                                                                                                                                                                             
            else:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           
                user = User.objects.create_user(user_name=username,email=email)
                user.save()
                info = User.objects.get(email=email)
                UserProfile.objects.filter(user_id=info.id).update(first_name=fname)
                UserProfile.objects.filter(user_id=info.id).update(last_name=lname)
                UserProfile.objects.filter(user_id=info.id).update(paypal_id=paypalid)
                
                return user

        except UserProfile.DoesNotExist:
            pass
        

            
    
    