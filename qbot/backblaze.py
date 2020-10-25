import hashlib
from dataclasses import dataclass
from typing import Optional

from b2sdk.bucket import Bucket
from b2sdk.v1 import B2Api, InMemoryAccountInfo

from qbot.core import registry
from qbot.db import b2_images
from vendor.imghdr import what


@dataclass
class Image:
    file_name: str
    hash: str
    url: str
    id: int
    exists: bool = False


def setup_b3(bucket: str, app_key_id: str, app_secret_key: str) -> Bucket:
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account(
        realm="production",
        application_key_id=app_key_id,
        application_key=app_secret_key,
    )
    return b2_api.get_bucket_by_name(bucket)


async def upload_image(
    content: bytes, plugin: str, bucket: Bucket, extra: Optional[str] = None
) -> Optional[Image]:
    extension = what("", h=content)
    if extension is None:
        return
    hasher = hashlib.sha1()
    hasher.update(content)
    sha1 = hasher.hexdigest()
    existing_image = await registry.database.fetch_one(
        b2_images.select().where(
            (b2_images.c.plugin == plugin) & (b2_images.c.hash == sha1)
        )
    )
    if existing_image is not None:
        return Image(
            file_name=existing_image["file_name"],
            hash=existing_image["hash"],
            url=existing_image["url"],
            id=existing_image["id"],
            exists=True,
        )
    file = bucket.upload_bytes(
        data_bytes=content,
        file_name=f"{plugin}_{sha1}.{extension}",
        file_infos={"plugin": plugin},
    )
    download_url = bucket.get_download_url(file.file_name)
    _id = await registry.database.execute(
        query=b2_images.insert(),
        values={
            "plugin": plugin,
            "file_name": file.file_name,
            "hash": file.content_sha1,
            "url": download_url,
            "extra": extra,
        },
    )
    image = Image(
        file_name=file.file_name, hash=file.content_sha1, url=download_url, id=_id
    )
    return image
