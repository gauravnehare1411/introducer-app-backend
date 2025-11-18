import aioboto3
from config.database import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_BUCKET_NAME, AWS_REGION

async def upload_to_s3_async(file, folder):
    session = aioboto3.Session()

    s3 = session.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

    file_ext = file.filename.split(".")[-1]
    key = f"{folder}/{file.filename}"

    async with s3 as s3_client:
        await s3_client.upload_fileobj(file.file, AWS_BUCKET_NAME, key)

    return key

async def generate_presigned_url(s3_key, expires_in=3600):
    session = aioboto3.Session()
    async with session.client("s3",
                              region_name=AWS_REGION,
                              aws_access_key_id=AWS_ACCESS_KEY_ID,
                              aws_secret_access_key=AWS_SECRET_ACCESS_KEY) as s3_client:
        url = await s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': AWS_BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=expires_in
        )
    return url

async def delete_customer_folder_s3(customer_id: str):
    """Delete all files inside the customer's S3 folder."""
    session = aioboto3.Session()
    prefix = f"{customer_id}/"

    async with session.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    ) as s3:
        
        response = await s3.list_objects_v2(
            Bucket=AWS_BUCKET_NAME,
            Prefix=prefix
        )

        if "Contents" not in response:
            return  # Nothing to delete

        delete_objects = {
            "Objects": [{"Key": obj["Key"]} for obj in response["Contents"]],
            "Quiet": True,
        }

        await s3.delete_objects(
            Bucket=AWS_BUCKET_NAME,
            Delete=delete_objects
        )

async def delete_from_s3_async(s3_key: str):
    session = aioboto3.Session()

    async with session.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    ) as s3_client:
        await s3_client.delete_object(
            Bucket=AWS_BUCKET_NAME,
            Key=s3_key
        )