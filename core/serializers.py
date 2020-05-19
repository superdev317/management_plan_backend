from drf_extra_fields.fields import (
    Base64ImageField as B64ImageField, Base64FileField as B64FileField 
)

from .utils import convert_file_to_base64 ,convert_file_to_s3url
import magic
import base64


class Base64ImageField(B64ImageField):
    """
    We want display image at base64 too
    """
    def to_representation(self, file):
        if not file:
            return
        return convert_file_to_base64(file)


class Base64FileField(B64FileField):
    """
    We want display file at base64 too
    """
    ALLOWED_TYPES = ['xlsx','pdf', 'txt', 'doc', 'docx', 'rtf','jpg','png','jpeg','ppt','pptx','zip']

    def to_representation(self, file):
        if not file:
            return
        if self.label == "notarized_document":
            return convert_file_to_s3url(file)
        else:
            return convert_file_to_base64(file)

    def get_file_extension(self, filename, decoded_file):
        mime = magic.Magic(mime=True)
        mtype = mime.from_buffer(decoded_file)
        base64_obj = base64.b64encode(decoded_file)
        if mtype.split('/')[1] == 'msword':
            return 'doc'
        if mtype.split('/')[1] == 'vnd.openxmlformats-officedocument.wordprocessingml.document':
            return 'docx'
        if mtype.split('/')[1] == 'plain':
            return 'txt'
        if mtype.split('/')[1] == 'vnd.openxmlformats-officedocument.presentationml.presentation':
            return 'pptx'
        if mtype.split('/')[1] == 'vnd.ms-powerpoint':
            return 'ppt'
        if mtype.split('/')[1] in ['vnd.openxmlformats-officedocument.spreadsheetml.sheet','octet-stream','zip']:
            return 'xlsx'
        else:
            return mtype.split('/')[1]
        # return 'xlsx'

    

