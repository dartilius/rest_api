import hashlib


class GetFileInfo:
    """Получение хешей файла."""

    @staticmethod
    def get_md5(file_path):
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as file:
            buffer = file.read()
            hash_md5.update(buffer)
        return hash_md5.hexdigest()

    @staticmethod
    def get_sha256(file_path):
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as file:
            buffer = file.read()
            hash_sha256.update(buffer)
        return hash_sha256.hexdigest()

    @staticmethod
    def get_length(file_path):
        pass

    @staticmethod
    def get_file_size(file_path):
        pass
