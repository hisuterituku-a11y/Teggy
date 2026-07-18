from core.metadata.metadata_service import MetadataService

file_path = r"X:\Работа\Радуга Здоровья\Фото\Teggy\XXXL (7).jpg"

metadata = MetadataService.read_metadata(file_path)
print("Title:", metadata.get('title'))
print("Subject:", metadata.get('subject'))