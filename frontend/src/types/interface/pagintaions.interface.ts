interface Pagination {
  page: number;
  limit: number;
}

export interface NomenclaturesPagination extends Pagination {
  search?: string;
  id?: string;
  versions?: string;
  status?: string;
  timezone?: string;
}

//TODO: Дописать остальные интерфейсы для пагинации