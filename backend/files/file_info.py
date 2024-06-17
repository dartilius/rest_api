import hashlib
import os
import subprocess
import tempfile
from datetime import timedelta


class GetFileInfo:
    """Получение хешей файла."""

    @staticmethod
    def get_md5(file):
        hash_md5 = hashlib.md5()
        file.seek(0)
        while chunk := file.read(8192):
            hash_md5.update(chunk)
        file.seek(0)
        return hash_md5.hexdigest()

    @staticmethod
    def get_sha256(file):
        hash_sha256 = hashlib.sha256()
        file.seek(0)
        while chunk := file.read(8192):
            hash_sha256.update(chunk)
        file.seek(0)
        return hash_sha256.hexdigest()

    @staticmethod
    def get_length(file):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        command = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            temp_file_path
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        os.remove(temp_file_path)
        try:
            duration_seconds = float(result.stdout.decode().strip())
            duration = timedelta(seconds=round(duration_seconds))
            return str(duration)
        except ValueError:
            return None

    @staticmethod
    def get_file_size(file):
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0, os.SEEK_SET)
        return size
