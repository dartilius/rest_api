import {
  UserInfo,
  UserInfoDTO,
  UsersList,
  UsersListDTO,
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
      role: user.role,
    })),
  };
};

export const userTransformer = (DTO: UserInfoDTO): UserInfo => {
  return {
    id: DTO.id,
    created: DTO.created,
    email: DTO.email,
    phoneNumber: DTO.phone_number,
    role: DTO.role,
    fullName: {
      firstName: DTO.full_name.first_name,
      lastName: DTO.full_name.last_name,
      middleName: DTO.full_name.middle_name,
    }
  }
}