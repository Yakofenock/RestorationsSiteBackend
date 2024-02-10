from storages.backends.s3boto3 import S3Boto3Storage


class JSFixedS3Boto3Storage(S3Boto3Storage):
    def get_object_parameters(self, name):
        params = super().get_object_parameters(name)
        if name.endswith('.js'):
            params['ContentType'] = 'application/javascript'
        return params
