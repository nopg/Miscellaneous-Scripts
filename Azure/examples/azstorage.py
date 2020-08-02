from azure.storage.fileshare import ShareClient

AZURE_STORAGE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=cnetpalopublic;AccountKey=hJAJfFZ7JLoACYja3dFmTYelw9cQnr3AkJzzf7Ig3QAG40IBWiWp8xDIW1XKh9/3lm81NBh1uBAO0YvZ3sSdqw==;EndpointSuffix=core.windows.net"
AZURE_STORAGE_ACCOUNT_NAME = "cnetpalopublic"
UPLOAD_FILE = './bst.xml'
DOWNLOAD_FILE = './downloaded.xml'


share = ShareClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING, "bootstrap")


dst_upload_file = share.get_file_client("bst.xml")
src_download_file = share.get_file_client("pfc/config/bootstrap.xml")
print("test")

# [START upload_file]
with open(UPLOAD_FILE, "rb") as source:
    dst_upload_file.upload_file(source)
# [END upload_file]

# Download the file
# [START download_file]
with open(DOWNLOAD_FILE, "wb") as data:
    stream = src_download_file.download_file()
    data.write(stream.readall())
# [END download_file]


# Delete the files
# [START delete_file]
dst_upload_file.delete_file()
# [END delete_file]
#my_allocated_file.delete_file()

# [START create_file]
# my_allocated_file = share.get_file_client("my_allocated_file")
# # Create and allocate bytes for the file (no content added yet)
# my_allocated_file.create_file(size=100)
# [END create_file]