import {
  TaskListResponse,
  TasksListResponseDTO,
} from "../interface/tasks.interface";

export const taskResponseTransformer = (
  DTO: TasksListResponseDTO,
): TaskListResponse => {
  return {
    count: DTO.count,
    next: DTO.next,
    previous: DTO.previous,
    results: DTO.results.map((task) => ({
      id: task.id,
      owner: {
        fullName: task.owner.full_name,
      },
      client: {
        name: task.client.name,
        id: task.client.id,
      },
      type: task.type,
      created: task.created,
      updated: task.updated,
      status: task.status,
    })),
  };
};
