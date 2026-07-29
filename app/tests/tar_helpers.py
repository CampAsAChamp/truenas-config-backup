import io
import tarfile


def make_tar_bytes(content: bytes = b"backup") -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        info = tarfile.TarInfo(name="config.txt")
        info.size = len(content)
        archive.addfile(info, io.BytesIO(content))
    return buffer.getvalue()
