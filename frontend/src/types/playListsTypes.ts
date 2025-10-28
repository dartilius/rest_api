export interface IPlayList {
  id: string
  name: string
  created: string
}

export interface IDataPlayListsResponse {
  count: number
  results: IPlayList[]
}

export interface IPlayListsDetail {
  id: string
  name: string
  description: string
  owner: {
    full_name: string
  }
  files: [
    {
      id: string
      name: string
      url: string
    },
  ]
  files_count: number
  created: string
}
