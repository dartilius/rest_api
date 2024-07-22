"use client";

import { useQuery } from "@tanstack/react-query";

import NomenclaturesList from "./NomenclaturesListClientPage";

import nomenclaturesService from "@/src/services/nomenclatures/nomenclatures.service";
import Loader from "@/src/components/ui/Loader";
import { toastError } from "@/src/utils/toast-error";

export default function ListPage() {
  const page: number = 1
  const limit: number = 10
  const { data, isLoading, error, isError, isSuccess } = useQuery({
    queryKey: ["nomenclaturesList"],
    queryFn: () => nomenclaturesService.getAll({page, limit}),
    select: ({ data }) => data,
  });

  if (isLoading) {
    return <Loader loading={!isSuccess} />;
  }

  if (isError) {
    return <>{toastError(error.message)}</>;
  }

  if (isSuccess) {
    return <NomenclaturesList />;
  }

  return <></>;
}
