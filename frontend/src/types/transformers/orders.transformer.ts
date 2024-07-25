import {
  AdOrdersListResponse,
  AdOrdersListResponseDTO,
  BgOrdersListResponse,
  BgOrdersListResponseDTO,
} from "../interface/orders.interface";

export const BgOrderResponseTransformer = (
  DTO: BgOrdersListResponseDTO,
): BgOrdersListResponse => {
  return {
    count: DTO.count,
    next: DTO.next,
    previous: DTO.previous,
    results: DTO.results.map((order) => ({
      id: order.id,
      name: order.name,
      status: order.status,
      broadcastInterval: {
        since: order.broadcast_interval.since,
        until: order.broadcast_interval.until,
      },
      client: {
        id: order.client.id,
        name: order.client.name,
      },
      playlist: {
        id: order.playlist.id,
        name: order.playlist.name,
      },
    })),
  };
};

export const AdOrderResponseTransformer = (
  DTO: AdOrdersListResponseDTO,
): AdOrdersListResponse => {
  return {
    count: DTO.count,
    next: DTO.next,
    previous: DTO.previous,
    results: DTO.results.map((order) => ({
      id: order.id,
      name: order.name,
      slides: order.slides,
      status: order.status,
      group: {
        id: order.group.id,
        name: order.group.name,
      },
      broadcastInterval: {
        since: order.broadcast_interval.since,
        until: order.broadcast_interval.until,
      },
      file: {
        id: order.file.id,
        name: order.file.name,
      },
    })),
  };
};
