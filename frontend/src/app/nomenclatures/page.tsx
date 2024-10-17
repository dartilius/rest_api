"use client";

import NomenclaturesList from "./NomenclaturesListClientPage";

import Loader from "@/src/components/ui/Loader";
import { toastError } from "@/src/utils/toast-error";
import useNomenclaturesQuery from "@/src/hooks/nomenclatures/useNomenclaturesQuery";

export default function Page() {
  const page = 1;
  const limit = 10;
  const { isLoading, error, isError, isSuccess } = useNomenclaturesQuery({
    page,
    limit,
  });

  if (isError) {
    return <>{toastError(error?.message)}</>;
  }

  if (isSuccess) {
    return <NomenclaturesList />;
  }

  return <></>;
}
