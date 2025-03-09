interface IClient {
    id: string
    name: string
  }
  interface IBroadcastInterval {
    lower: string
    upper: string
  }
  
 export interface IBgData {
    id: string
    name: string
    client: IClient
    order_type: number
    status: number
    broadcast_interval: IBroadcastInterval
  }
 export interface IAdData {
    id: string
    name: string
    client: IClient
    broadcast_type: number
    status: number
    broadcast_interval: IBroadcastInterval
  }

  export interface IDataBgResponse {
    count: number;
    next: string | null;
    previous: string | null;
    results: IBgData[];
  }
  

  
  export interface IDataAdResponse {
    count: number;
    next: string | null;
    previous: string | null;
    results: IAdData[];
  }
  