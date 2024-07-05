import {
  TagResponse,
  TagResponseDTO,
  TagsListResponse,
  TagsListResponseDTO,
} from "../interface/tags.interface";

export const tagsListResponseTransformer = (
  DTO: TagsListResponseDTO,
): TagsListResponse => {
  return {
    count: DTO.count,
    next: DTO.next,
    previous: DTO.previous,
    results: DTO.results,
  };
};

export const tagResponseTransformer = (DTO: TagResponseDTO): TagResponse => {
  return {
    id: DTO.id,
    name: DTO.name,
  };
};
