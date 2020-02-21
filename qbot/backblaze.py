import imghdr
from dataclasses import dataclass

from b2sdk.bucket import Bucket
from b2sdk.v1 import B2Api, InMemoryAccountInfo


@dataclass
class Image:
    external_id: str
    file_name: str
    mime_type: str
    hash: str


def setup_b3(bucket: str, app_key_id: str, app_secret_key: str) -> Bucket:
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account(
        realm="production",
        application_key_id=app_key_id,
        application_key=app_secret_key,
    )
    return b2_api.get_bucket_by_name(bucket)


def upload_image(content: bytes, base_name: str, plugin: str, bucket: Bucket) -> Image:
    extension = imghdr.what("", h=content)
    file = bucket.upload_bytes(
        data_bytes=content,
        file_name=f"{base_name}.{extension}",
        file_infos={"plugin": plugin},
    )
    return Image(
        external_id=file.id_,
        file_name=file.file_name,
        mime_type=file.content_type,
        hash=file.content_sha1,
    )
