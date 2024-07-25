"use client";

import NomenclaturesList from "./NomenclaturesListClientPage";

import Loader from "@/src/components/ui/Loader";
import { toastError } from "@/src/utils/toast-error";
import useNomenclaturesQuery from "@/src/hooks/nomenclatures/useNomenclaturesQuery";

export default function ListPage() {
  const page = 1;
  const limit = 10;
  const { isLoading, error, isError, isSuccess } = useNomenclaturesQuery({
    page,
    limit,
  });

  if (isLoading) {
    return <Loader loading={!isSuccess} />;
  }

  if (isError) {
    return <>{toastError(error?.message)}</>;
  }

  if (isSuccess) {
    return <NomenclaturesList />;
  }

  return <></>;
}
