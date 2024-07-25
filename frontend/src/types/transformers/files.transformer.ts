import {
  FileResponse,
  FileResponseDTO,
  FilesCreateRequest,
  FilesCreateRequestDTO,
  FilesCreateResponse,
  FilesCreateResponseDTO,
  FilesListResponse,
  FilesListResponseDTO,
  ReadFileResponse,
  ReadFileResponseDTO,
  UpdateFileRequest,
  UpdateFileRequestDTO,
} from "../interface/files.interface";

export const filesResponseTransformer = (
  DTO: FileResponseDTO,
): FileResponse => {
  return {
    fileType: DTO.file_type,
    id: DTO.id,
    length: DTO.length,
    name: DTO.name,
    size: DTO.size,
    tags: DTO.tags,
  };
};

export const filesListResponseTransformer = (
  DTO: FilesListResponseDTO,
): FilesListResponse => {
  return {
    count: DTO.count,
    next: DTO.next,
    previous: DTO.previous,
    results: DTO.results.map(filesResponseTransformer),
  };
};

export const filesCreateRequestTransformer = (
  request: FilesCreateRequest,
): FilesCreateRequestDTO => {
  return {
    // name: request.name,
    file_type: request.fileType,
    tags: request.tags,
    source: request.source,
  };
};

export const filesCreateResponseTransformer = (
  DTO: FilesCreateResponseDTO,
): FilesCreateResponse => {
  return {
    id: DTO.id,
    name: DTO.name,
    hash: DTO.hash,
    created: DTO.created,
    fileType: DTO.file_type,
    length: DTO.length,
    size: DTO.size,
    tags: DTO.tags,
  };
};

export const readFileResponseTransformer = (
  DTO: ReadFileResponseDTO,
): ReadFileResponse => {
  return {
    id: DTO.id,
    name: DTO.name,
    length: DTO.length,
    size: DTO.size,
    fileType: DTO.file_type,
    tags: DTO.tags,
    hash: {
      md5: DTO.hash.md5,
      concatHash: DTO.hash.concat_hash,
      sha256: DTO.hash.sha256,
    },
  };
};

export const fileUpdateRequestTransformer = (
  request: UpdateFileRequest,
): UpdateFileRequestDTO => {
  return {
    file_type: request.fileType,
    tags: request.tags,
  };
};
