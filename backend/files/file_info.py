import hashlib
import os
import subprocess
import tempfile
from datetime import timedelta as td


class GetFileInfo:
    """Получение параметров файла."""

    @staticmethod
    def get_md5(file) -> str:
        """
        Вычисление md5 хэша.

        1. Ставим курсор в начале файла
        2. Проходим по файлу отрезками в 8Кб, пока он не закончится
        3. Возвращаем хеш по всему содержимому файла
        """
        hash_md5 = hashlib.md5()
        file.seek(0)
        while chunk := file.read(8192):
            hash_md5.update(chunk)
        file.seek(0)
        return hash_md5.hexdigest()

    @staticmethod
    def get_sha256(file) -> str:
        """
        Вычисление sha256 хэша.

        1. Ставим курсор в начале файла
        2. Проходим по файлу отрезками в 8Кб, пока он не закончится
        3. Возвращаем хеш по всему содержимому файла
        """
        hash_sha256 = hashlib.sha256()
        file.seek(0)
        while chunk := file.read(8192):
            hash_sha256.update(chunk)
        file.seek(0)
        return hash_sha256.hexdigest()

    @staticmethod
    def get_length(file) -> str | None:
        """
        Вычисление продолжительности файла с помощью ffmpeg.

        1. Из полученных данных создаётся временный файл
        2. Временный файл проходит команду для вычисления продолжительности
        3. Результат записывается, временный файл удаляется
        4. Результат округляется до целых секунд
        5. При нулевой продолжительности (например у картинок)
            возникает ValueError, возвращается None
        """
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        command = ['mediainfo',
                   '--Inform=General;%Duration%',
                   temp_file_path]
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        os.remove(temp_file_path)
        try:
            microseconds = int(result.stdout.decode().strip())
            duration = td(seconds=round(microseconds/1000))
            return str(duration)
        except ValueError:
            return None

    @staticmethod
    def get_file_size(file) -> int:
        """
        Вычисление размера файла.

        1. Ставим курсор в конец файла
        2. Записываем количество байт, которое прошли
        3. Возвращаем курсор в начало файла
        """
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0, os.SEEK_SET)
        return size
