"use client";

import {
  Button,
  Card,
  CardBody,
  CardFooter,
  CardHeader,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableColumn,
  TableHeader,
  TableRow,
} from "@nextui-org/react";
import { useEffect, useState } from "react";

import DeletingModal from "../../../components/ui/DeletingModal";

import TranscriptData from "./components/TranscriptData";
import EditingModal from "./components/EditingModal";

import {
  DaySettings,
  NomenclatureInterface,
} from "@/src/types/interface/nomenclature.interface";
import Loader from "@/src/components/ui/Loader";
import { toastSuccess } from "@/src/utils/toast-success";
import { toastError } from "@/src/utils/toast-error";
import { useDeleteNomenclatureQuery } from "@/src/hooks/nomenclatures/useNomenclatureQuery";
import useIdFromParams from "@/src/hooks/useIdFromParams";

type Props = {
  id: string | undefined;
  data: NomenclatureInterface | undefined;
};

const dayNames: Record<string, string> = {
  mon: "Понедельник",
  tue: "Вторник",
  wed: "Среда",
  thu: "Четверг",
  fri: "Пятница",
  sat: "Суббота",
  sun: "Воскресенье",
};

export default function NomenclatureDetails(props: Props) {
  const { data } = props;
  const id = useIdFromParams();

  const [openEditingModal, setOpenEditingModal] = useState<boolean>(false);
  const [openDeletingModal, setOpenDeletingModal] = useState<boolean>(false);
  const {
    mutateAsync: deleteNomenclature,
    isSuccess: isDeleteSuccess,
    error: deleteError,
    isError: isDeleteError,
  } = useDeleteNomenclatureQuery();

  useEffect(() => {
    if (isDeleteSuccess) {
      toastSuccess("Номенклатура успешно удалена");
      setTimeout(() => {
        window.location.replace("/nomenclatures");
      }, 2500);
    }
  }, [isDeleteSuccess]);

  const handleDeleteNomenclature = () => {
    deleteNomenclature(id);
  };

  if (isDeleteError) {
    return <>{toastError(deleteError?.message)}</>;
  }

  if (!data) {
    return <Loader />;
  }

  const renderSettingsTable = (
    settings: Record<string, DaySettings | undefined>,
  ) => {
    const sortedSettings = Object.entries(settings)
      .filter(([day, setting]) => setting !== undefined)
      .sort(([dayA], [dayB]) => dayNames[dayA].localeCompare(dayNames[dayB]));

    return (
      <Table aria-label="Settings Table">
        <TableHeader>
          <TableColumn>День</TableColumn>
          <TableColumn>Рабочее время</TableColumn>
          <TableColumn>Уровень громкости</TableColumn>
        </TableHeader>
        <TableBody>
          {sortedSettings.map(([day, setting]) => (
            <TableRow key={day}>
              <TableCell>{dayNames[day]}</TableCell>
              <TableCell>{setting?.worktime.join(" - ")}</TableCell>
              <TableCell>{setting?.default_volume.join(", ")}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    );
  };

  const handleCloseEditingModal = () => {
    setOpenEditingModal(false);
  };
  const handleCloseDeletingModal = () => {
    setOpenDeletingModal(false);
  };

  return (
    <div>
      <Card className="w-auto">
        <CardHeader className="flex justify-center">
          <h1>{data?.name}</h1>
        </CardHeader>
        <Divider />
        <CardBody className="flex items-center">
          <TranscriptData data={data.id} label="id" />
          <TranscriptData data={data.description} label="Описание" />
          <TranscriptData data={data.last_answer} label="Последний ответ" />
          <TranscriptData data={data.owner} label="Владелец" />
          <TranscriptData data={data.status} label="Статус" />
          <TranscriptData data={data.version} label="Версия" />
          <TranscriptData data={data.timezone} label="timezone" />
          <TranscriptData data={data.hw_info} label="Инфо тачки" />
        </CardBody>
        <Divider />
        <CardFooter className="flex flex-col gap-3">
          {renderSettingsTable(data.settings)}
          <div
            style={{
              maxWidth: "8rem",
              width: "100%",
              display: "flex",
              flexDirection: "column",
              gap: "1rem",
            }}
          >
            <Button
              color="primary"
              style={{ width: "100%" }}
              onClick={() => setOpenEditingModal(true)}
            >
              Редактировать
            </Button>
            <Button
              color="danger"
              style={{ width: "100%" }}
              onClick={() => setOpenDeletingModal(true)}
            >
              Удалить
            </Button>
          </div>
        </CardFooter>
      </Card>
      <EditingModal
        close={handleCloseEditingModal}
        data={data}
        id={data.id}
        open={openEditingModal}
      />
      <DeletingModal
        close={handleCloseDeletingModal}
        deleteProp={handleDeleteNomenclature}
        open={openDeletingModal}
      />
    </div>
  );
}
