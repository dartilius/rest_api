import { API_URL } from "../../config/api.config";
import {
  TaskListResponse,
  TasksListResponseDTO,
} from "../../types/interface/tasks.interface";
import { taskResponseTransformer } from "../../types/transformers/tasks.transforems";

interface Pagination {
  page?: number;
  limit?: number;
}

export const TasksService = {
  async getAll(props: Pagination): Promise<TaskListResponse> {
    const { page, limit } = props;
    let url = `${API_URL}/api/tasks/`;

    if (page !== undefined) {
      url += `?page=${page}`;
    }
    if (limit !== undefined) {
      url += `&limit=${limit}`;
    }
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (response.ok) {
      const data: TasksListResponseDTO = await response.json(); // Используем TasksListResponseDTO для данных из API

      console.log(data);

      return taskResponseTransformer(data); // Преобразуем данные в TaskListResponse
    } else {
      throw new Error("Не удалось получить список задач");
    }
  },
};
