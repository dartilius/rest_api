"use client";

import { useParams } from "next/navigation";

import { useNomenclaturesDetails } from "../../hooks/nomenclatures/useNomenclaturesDetails";

export default function NomenclatureDetails() {
  const router = useParams();
  const id = router.id;
  const { data } = useNomenclaturesDetails(id);

  console.log(data);

  return <div />;
}
