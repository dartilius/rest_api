import {
  GroupsListResponse,
  GroupsListResponseDTO,
} from "../interface/groups.interface";

export const groupsListResponseTransformer = (
  DTO: GroupsListResponseDTO,
): GroupsListResponse => {
  return {
    count: DTO.count,
    next: DTO.next,
    previous: DTO.previous,
    results: DTO.results.map((group) => ({
      id: group.id,
      name: group.name,
      clientsCount: group.clients_count,
      created: group.created,
    })),
  };
};
