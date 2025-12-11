# Diary Module - Document Upload Guide

## Overview
The Diary module supports document uploads similar to the Opportunity module. Documents are stored using a separate REST API for file storage, and the diary module stores the document IDs which are then converted to presigned URLs when queried.

## Document Upload Flow

### 1. Upload Files to Storage Server
First, upload your files (PDFs, Word docs, images, etc.) to your file storage REST API endpoint. This will return file IDs.

**Example:**
```
POST /api/upload/documents
Content-Type: multipart/form-data

Response:
{
  "file_ids": ["doc_abc123", "doc_xyz789"]
}
```

### 2. Create Diary Document with File IDs

Once you have the file IDs, create a diary document entry:

```graphql
mutation CreateDiaryDocument {
  createDiaryDocument(input: {
    title: "Project Documentation"
    description: "Important project files and specifications"
    folderUid: "folder_uid_here"
    documentIds: ["doc_abc123", "doc_xyz789"]
    privacyLevel: PRIVATE
  }) {
    success
    message
    document {
      uid
      title
      description
      documentIds
      documentUrls {
        fileId
        url
        fileName
        fileType
        fileSize
      }
      privacyLevel
      createdOn
      updatedOn
    }
  }
}
```

### 3. Query Documents with Presigned URLs

When you query documents, the `documentUrls` field automatically generates presigned URLs:

```graphql
query MyDiaryDocuments {
  myDiaryDocuments(folderUid: "folder_uid_here") {
    uid
    title
    description
    documentIds
    documentUrls {
      fileId
      url          # Presigned URL for direct download
      fileName
      fileType
      fileSize
    }
    folder {
      uid
      name
    }
    createdOn
  }
}
```

## Key Features

### Multiple Documents Support
- Each diary document can have **multiple files** attached
- Store PDFs, Word docs, images, spreadsheets, etc.
- All files are returned with presigned URLs for secure access

### Document IDs vs Document URLs
- **documentIds**: Array of raw file IDs stored in the database
- **documentUrls**: Array of `FileDetailType` objects with presigned URLs generated on-the-fly

### FileDetailType Structure
```graphql
type FileDetailType {
  fileId: String
  url: String        # Presigned URL (temporary, secure)
  fileName: String
  fileType: String
  fileSize: Int
}
```

## Update Documents

You can update document files by providing new document IDs:

```graphql
mutation UpdateDiaryDocument {
  updateDiaryDocument(input: {
    uid: "document_uid_here"
    title: "Updated Title"
    documentIds: ["doc_new123", "doc_new456"]  # Replace with new files
  }) {
    success
    message
    document {
      uid
      documentUrls {
        fileId
        url
        fileName
      }
    }
  }
}
```

## Privacy Levels

Documents support privacy levels:
- **PRIVATE**: Only you can see
- **INNER**: Inner circle can see
- **OUTER**: Outer circle can see
- **UNIVERSE**: Everyone can see

## Best Practices

1. **Upload files first** to your storage server before creating diary documents
2. **Store file IDs** returned from the upload endpoint
3. **Use document_ids** when creating/updating diary documents
4. **Query document_urls** to get presigned URLs for displaying/downloading files
5. **Validate file types** on the frontend before upload
6. **Handle upload errors** gracefully with user feedback

## Example Complete Flow

```javascript
// 1. Upload files
const formData = new FormData();
formData.append('file1', file1);
formData.append('file2', file2);

const uploadResponse = await fetch('/api/upload/documents', {
  method: 'POST',
  body: formData
});

const { file_ids } = await uploadResponse.json();

// 2. Create diary document with file IDs
const createMutation = `
  mutation CreateDiaryDocument($input: CreateDiaryDocumentInput!) {
    createDiaryDocument(input: $input) {
      success
      message
      document {
        uid
        documentUrls {
          url
          fileName
        }
      }
    }
  }
`;

const result = await graphqlClient.mutate({
  mutation: createMutation,
  variables: {
    input: {
      title: "My Documents",
      folderUid: folderUid,
      documentIds: file_ids
    }
  }
});

// 3. Display documents with presigned URLs
result.data.createDiaryDocument.document.documentUrls.forEach(doc => {
  console.log(`Download: ${doc.fileName} from ${doc.url}`);
});
```

## Notes

- Presigned URLs are **temporary** and expire after a certain time
- Always query `documentUrls` when you need to display/download files
- The `documentIds` field is useful for tracking which files are attached
- Multiple documents can be attached to a single diary document entry
