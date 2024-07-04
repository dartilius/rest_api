import {
  UsersListResponse,
  UsersListResponseDTO,
} from "../interface/user.interface";

export const userResponseTransformer = (
  DTO: UsersListResponseDTO,
): UsersListResponse => {
  return {
    count: DTO.count,
    next: DTO.next,
    previous: DTO.previous,
    results: DTO.results.map((user) => ({
      id: user.id,
      created: user.created,
      fullName: user.full_name,
    })),
  };
};
