from pyiceberg.catalog import load_catalog


def get_catalog():
    return load_catalog(
        "rest",
        **{
            "uri": "http://localhost:8181",
            "s3.endpoint": "http://minio:9000",
            "s3.access-key-id": "admin",
            "s3.secret-access-key": "password",
            "s3.path-style-access": "true",
            "s3.region": "us-east-1",
        },
    )