"use client";

import { useParams } from "next/navigation";

import { useNomenclaturesDetails } from "../../hooks/nomenclatures/useNomenclaturesDetails";

import NomenclatureDetails from "./NomenclatureDetails";

import Loader from "@/src/components/ui/Loader";
import { toastError } from "@/src/utils/toast-error";

export default function NomenclaturePage() {
  const router = useParams();
  const id = router.id;
  const { isLoading, error, isError, isSuccess } = useNomenclaturesDetails(id);

  if (isLoading) {
    return <Loader loading={!isSuccess} />;
  }

  if (isError) {
    return <>{toastError(error?.message)}</>;
  }

  if (isSuccess) {
    return <NomenclatureDetails />;
  }

  return <></>;
}
