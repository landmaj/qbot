import hashlib
import imghdr
from dataclasses import dataclass

from b2sdk.bucket import Bucket
from b2sdk.v1 import B2Api, InMemoryAccountInfo


@dataclass
class Image:
    file_name: str
    mime_type: str
    hash: str
    url: str


def setup_b3(bucket: str, app_key_id: str, app_secret_key: str) -> Bucket:
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account(
        realm="production",
        application_key_id=app_key_id,
        application_key=app_secret_key,
    )
    return b2_api.get_bucket_by_name(bucket)


def upload_image(content: bytes, plugin: str, bucket: Bucket) -> Image:
    hasher = hashlib.sha1()
    hasher.update(content)
    sha1 = hasher.hexdigest()
    extension = imghdr.what("", h=content)
    file = bucket.upload_bytes(
        data_bytes=content,
        file_name=f"{plugin}_{sha1}.{extension}",
        file_infos={"plugin": plugin},
    )
    download_url = bucket.get_download_url(file.file_name)
    return Image(
        file_name=file.file_name,
        mime_type=file.content_type,
        hash=file.content_sha1,
        url=download_url,
    )
