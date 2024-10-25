"use client";

import NomenclatureDetails from "./NomenclatureDetails";

import Loader from "@/src/components/ui/Loader";
import { useNomenclatureQuery } from "@/src/hooks/nomenclatures/useNomenclatureQuery";
import { toastError } from "@/src/utils/toast-error";

type Props = {
  id: string;
};

export default function ListPage(props: Props) {
  const { id } = props;
  const { data, isLoading, error, isError, isSuccess } = useNomenclatureQuery(
    id?.toString() || "",
  );

  if (isLoading) {
    return <Loader loading={!isSuccess} />;
  }

  if (isError) {
    return <>{toastError(error?.message)}</>;
  }

  if (isSuccess) {
    return <NomenclatureDetails id={id} />;
  }

  return <></>;
}
