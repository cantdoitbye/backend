from auth_manager.Utils import generate_presigned_url
import time

class FileURL:
    _file_url_map = {}

    @classmethod
    def store_file_urls(cls, file_ids):
        """
        Fetch and store URLs for a list of file IDs.
        """
        for file_id in file_ids:
            if file_id not in cls._file_url_map:
                file_url = generate_presigned_url.generate_file_info(file_id)
                cls._file_url_map[file_id] = file_url

    @classmethod
    def get_file_url(cls, file_id):
        """
        Retrieve the cached URL for a specific file ID.
        """
        
        if file_id not in cls._file_url_map:
            raise ValueError(f"File URL not found for file_id: {file_id}. Make sure to call `store_file_urls` first.")
        
        
        return cls._file_url_map[file_id]