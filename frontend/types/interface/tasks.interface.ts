export type TasksListResponseDTO = {
  count: number;
  next: string | null;
  previous: string | null;
  results: TaskDTO[];
};

export type TaskDTO = {
  id: string;
  owner: OwnerTaskDTO;
  client: ClientTaskDTO;
  type: number;
  created: string;
  updated: string;
  status: number;
};

export type TaskListResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: Task[];
};

export type Task = {
  id: string;
  owner: OwnerTask;
  client: ClientTask;
  type: number;
  created: string;
  updated: string;
  status: number;
};

type ClientTaskDTO = {
  id: string;
  name: string;
}

type ClientTask = {
  id: string;
  name: string;
}

type OwnerTaskDTO = {
    full_name: string;
}
type OwnerTask = {
    fullName: string;
}
