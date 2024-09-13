export interface TagResponseInterface {
  id: number;
  name: string;
}

export interface TagsListInterface {
  count: number;
  next: string;
  previous: string;
  results: TagResponseInterface[];
}