# `client.library`

Manage live response library files.

## Property

`client.library`

## Methods

- `get_all() -> LibraryFilesResults`: list live response library files.
- `upload(payload: LibraryFilesUpdatePayload) -> bool`: upload a library file.
- `delete(file_name: str) -> bool`: delete a library file.

## Notes

- `upload()` and `delete()` return booleans rather than results wrappers.
- `LibraryFilesUpdatePayload` includes file metadata such as `file_name`, `file_content`, `content_type`, and descriptions.
