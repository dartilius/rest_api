export type AdOrdersListResponseDTO = {
  previous: string | null;
  next: string | null;
  count: number;
  results: AdOrderResponseDTO[];
};

export type AdOrdersListResponse = {
  previous: string | null;
  next: string | null;
  count: number;
  results: AdOrderResponse[];
};

export type AdOrderResponseDTO = {
  id: number;
  name: string;
  status: number;
  slides: []
  broadcast_interval: {
    since: string;
    until: string;
  }
  file: {
    id: string;
    name: string;
  }
  group: {
    id: number;
    name: string;
  }
};

export type AdOrderResponse = {
  id: number;
  name: string;
  status: number;
  slides: []
  broadcastInterval: {
    since: string;
    until: string;
  }
  file: {
    id: string;
    name: string;
  }
  group: {
    id: number;
    name: string;
  }
};

export type BgOrdersListResponseDTO = {
  previous: string | null;
  next: string | null;
  count: number;
  results: BgOrderResponseDTO[];
};

export type BgOrdersListResponse = {
  previous: string | null;
  next: string | null;
  count: number;
  results: BgOrderResponse[];
};

export type BgOrderResponseDTO = {
  id: number;
  name: string;
  status: number;
  broadcast_interval: {
    since: string;
    until: string;
  };
  client: {
    id: string;
    name: string;
  };
  playlist: {
    id: number;
    name: string;
  };
};

export type BgOrderResponse = {
  id: number;
  name: string;
  status: number;
  broadcastInterval: {
    since: string;
    until: string;
  };
  client: {
    id: string;
    name: string;
  };
  playlist: {
    id: number;
    name: string;
  };
};
