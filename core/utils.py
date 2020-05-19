import magic
import base64
from io import BytesIO,StringIO
import boto
from saffron_backend import settings
from boto.s3.key import Key
import sys,re
from boto.s3.connection import S3Connection
from saffron_backend.settings import *




def convert_file_to_base64(obj):
    """
    Function for convert files to base64
    """
    mime = magic.Magic(mime=True)
    read_obj = obj.read()
    mtype = mime.from_buffer(read_obj)
    base64_obj = base64.b64encode(read_obj)

    return 'data:{};base64,{}'.format(mtype, base64_obj.decode("utf-8"))

def convert_file_to_s3url(obj):
    """
    Function for convert files to s3url
    """
    #base64 loading time was high so we replaced this function to get
    #one time url images from amazon reducing loading speed by 30%

    conn = S3Connection(AWS_ACCESS_KEY_ID,AWS_SECRET_ACCESS_KEY,host=AWS_HOST)
    #connecting to aws with specific endpoint reason
    bucket = conn.get_bucket(AWS_S3_BUCKET_NAME)
    #getting bucket from AWS
    key = bucket.get_key(obj.name, validate=True)
    url = key.generate_url(900)
    #generating url with expiration time
    return "{}".format(url)