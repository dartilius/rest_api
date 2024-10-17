import {TagsListResponseDTO} from "@/src/types/interface/tags.interface";

export type FilesListResponseDTO = {
  results: FileResponseDTO[];
  next: string;
  previous: string;
  count: number;
};

export type FileResponseDTO = {
  id: string;
  name: string;
  length: string;
  size: number;
  file_type: number;
  tags: string[];
};

export type FileResponse = {
  id: string;
  name: string;
  length: string;
  size: number;
  file_type: number;
  tags: string[];
};

export type FilesListResponse = {
  results: FileResponse[];
  next: string;
  previous: string;
  count: number;
};

export type FilesCreateRequestDTO = {
  // name: string;
  file_type: number;
  tags: number[];
  source: string;
};

export type FilesCreateRequest = {
  file_type: number;
  tags?: number[];
  source: string[];
};

export interface ITagsList {
  count: number;
  next: string;
  previous: string;
  results: ITagsListResponseDTO[];
}

export type ITagsListResponseDTO = {
  id: number;
  name: string;
}

export type FilesCreateResponseDTO = {
  id: string;
  name: string;
  hash: string;
  length: string;
  size: number;
  file_type: number;
  tags: string[];
  created: string;
};
export type FilesCreateResponse = {
  id: string;
  name: string;
  hash: string;
  length: string;
  size: number;
  fileType: number;
  tags: string[];
  created: string;
};

export type TagsCreateRequest = {
  name: string;
};

export type TagsCreateResponse = {
  id: string;
  name: string;
};

export type ReadFileResponseDTO = {
  id: string;
  name: string;
  length: string;
  size: number;
  file_type: number;
  tags: string[];
  hash: {
    md5: string;
    sha256: string;
    concat_hash: string;
  };
};

export type ReadFileResponse = {
  id: string;
  name: string;
  length: string;
  size: number;
  fileType: number;
  tags: any;
  hash: {
    md5: string;
    sha256: string;
    concat_hash: string;
  };
  url: string;
};

export type UpdateFileRequest = {
  fileType: string;
  tags: string[];
};

export type UpdateFileRequestDTO = {
  file_type: string;
  tags: string[];
};