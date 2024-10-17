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

import styles from './NomenclatureDetails.module.scss'

import {
  DaySettings,
  NomenclatureInterface,
} from "@/src/types/interface/nomenclature.interface";
import Loader from "@/src/components/ui/Loader";
import { toastSuccess } from "@/src/utils/toast-success";
import { toastError } from "@/src/utils/toast-error";
import { useDeleteNomenclatureQuery } from "@/src/hooks/nomenclatures/useNomenclatureQuery";
import useIdFromParams from "@/src/hooks/useIdFromParams";
import CustomTextarea from "@/src/app/nomenclatures/[id]/components/CustomTextArea";
import {convertStatus} from "@/src/types/types/checkStatus";
import {convertZone, timezonesArray} from "@/src/types/types/timezone";

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

function parseStringData(data: any | undefined) {
  if (!data) return
  return JSON.parse(data.replace(/'/g, '"'));
}

export default function NomenclatureDetails(props: Props) {
  const { data } = props;
  const id = useIdFromParams();
  const [edit, setEdit] = useState<boolean>(false)

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
      // .filter(([day, setting]) => setting !== undefined)
      .sort(([dayA], [dayB]) => dayNames[dayA].localeCompare(dayNames[dayB]));

    return (
      <Table aria-label="Settings Table" width='auto'>
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

  const interfaces = parseStringData(data.hw_info?.interfaces);

// Парсим audiodevices
  const audiodevices = parseStringData(data.hw_info?.audiodevices);

// Парсим sd_card_data
  const sd_card_data = parseStringData(data.hw_info?.sd_card_data);

// Выводим результаты
  console.log('Interfaces:', interfaces);
  console.log('Audio Devices:', audiodevices);
  console.log('SD Card Data:', sd_card_data);

  return (
      <div className={styles.container}> {/*container*/}
        <div className={styles.container_upperBlock}> {/*block main and hw*/}
          <div className={styles.container_upperBlock_mainInfo}>
            <span className={styles.container_upperBlock_mainInfo_name}>{data.main_info.name}</span>
            <CustomTextarea placeholder='Описание' desc={data.main_info.description}/>
            {data.main_info.status !== null &&
                <div className={styles.container_upperBlock_mainInfo_status}>
                <span className={styles.container_upperBlock_mainInfo_status_offline}>
                  {convertStatus(data.main_info.status)}
                </span>
                </div>
            }
            {(data.main_info.status === 1 || data.main_info.status === 2) &&
                <div className={styles.container_upperBlock_mainInfo_lastOnline}>
                <span
                    className={styles.container_upperBlock_mainInfo_lastOnline_label}>Время последнего ответа:&nbsp;</span>
                  {data.main_info.last_answer}
                </div>
            }
            {data.main_info.status === null &&
                <span className={styles.container_upperBlock_mainInfo_status_offline}>Не выходила в сеть</span>}
            {data.main_info.version !== '' &&
                <div className={styles.container_upperBlock_mainInfo_versionBlock}>
                  <span className={styles.container_upperBlock_mainInfo_versionBlock_label}>Весрия ПО:&nbsp;</span>
                  {data.main_info.version}
                </div>
            }
            <div className={styles.container_upperBlock_mainInfo_timezoneBlock}>
              <span className={styles.container_upperBlock_mainInfo_timezoneBlock_label}>Часовой пояс:&nbsp;</span>
              {convertZone(data.main_info.timezone)}
            </div>


          </div>
          <div className={styles.container_upperBlock_hwInfo}>
            <div>
              <strong>Model:</strong> {data.hw_info?.model}
            </div>
            <div>
              <strong>Revision:</strong> {data.hw_info?.revision}
            </div>
            <div>
              <strong>Interfaces:</strong>
              <ul>
                {interfaces?.map((iface: any, index: any) => (
                    <li key={index}>
                      {iface.iface} - MAC: {iface.mac}, IP: {iface.ip || "N/A"}
                    </li>
                ))}
              </ul>
            </div>
            <div>
              <strong>Audio Devices:</strong>
              <ul>
                {audiodevices?.map((device: any, index: any) => (
                    <li key={index}>
                      Card {device?.card}: {device?.name}
                    </li>
                ))}
              </ul>
            </div>
            <div>
              <strong>SD Card Data:</strong> {sd_card_data?.name}, Manufacturer ID: {sd_card_data?.manf_id}
            </div>
          </div>

        </div>


        {/*<div className={styles.container_lowerBlock_settingsBlock}>*/}
        {/*  /!*{renderSettingsTable(data.settings)}*!/*/}
        {/*  <div className={styles.container_lowerBlock_settingsBlock_start}>Время работы</div>*/}
        {/*  <div className={styles.container_lowerBlock_settingsBlock_volume}>Стандартная громкость</div>*/}
        {/*  <div className={styles.container_lowerBlock_settingsBlock_monday}>Понедельник</div>*/}
        {/*  <div*/}
        {/*      className={styles.container_lowerBlock_settingsBlock_monday_time}>{data.settings.mon?.worktime?.join(" - ")}</div>*/}
        {/*  <div*/}
        {/*      className={styles.container_lowerBlock_settingsBlock_monday_volume}>{data.settings.mon?.default_volume?.join(", ")}</div>*/}
        {/*  <div className={styles.container_lowerBlock_settingsBlock_tuesday}>Вторник</div>*/}
        {/*  <div className={styles.container_lowerBlock_settingsBlock_tuesday_time}>*/}
        {/*    {data.settings.tue?.worktime.join(" - ")}*/}
        {/*  </div>*/}
        {/*  <div className={styles.container_lowerBlock_settingsBlock_tuesday_volume}>*/}
        {/*    {data.settings.tue?.default_volume.join(", ")}*/}
        {/*  </div>*/}
        {/*  <div className={styles.container_lowerBlock_settingsBlock_wednesday}>Среда</div>*/}
        {/*  <div className={styles.container_lowerBlock_settingsBlock_wednesday_time}>*/}
        {/*    {data.settings.wed?.worktime.join(" - ")}*/}
        {/*  </div>*/}
        {/*  <div className={styles.container_lowerBlock_settingsBlock_wednesday_volume}>*/}
        {/*    {data.settings.wed?.default_volume.join(", ")}*/}
        {/*  </div>*/}
        {/*  <div className={styles.container_lowerBlock_settingsBlock_thusday}>Четверг</div>*/}
        {/*  <div className={styles.container_lowerBlock_settingsBlock_thusday_time}>*/}
        {/*    {data.settings.thu?.worktime.join(" - ")}*/}
        {/*  </div>*/}
        {/*  <div className={styles.container_lowerBlock_settingsBlock_thusday_volume}>*/}
        {/*    {data.settings.thu?.default_volume.join(", ")}*/}
        {/*  </div>*/}
        {/*  <div className={styles.container_lowerBlock_settingsBlock_friday}>Пятница</div>*/}
        {/*  <div className={styles.container_lowerBlock_settingsBlock_friday_time}>*/}
        {/*    {data.settings.fri?.worktime.join(" - ")}*/}
        {/*  </div>*/}
        {/*  <div className={styles.container_lowerBlock_settingsBlock_friday_volume}>*/}
        {/*    {data.settings.fri?.default_volume.join(", ")}*/}
        {/*  </div>*/}
        {/*  <div className={styles.container_lowerBlock_settingsBlock_saturday}>Суббота</div>*/}
        {/*  <div className={styles.container_lowerBlock_settingsBlock_saturday_time}>*/}
        {/*    {data.settings.sat?.worktime.join(" - ")}*/}
        {/*  </div>*/}
        {/*  <div className={styles.container_lowerBlock_settingsBlock_saturday_volume}>*/}
        {/*    {data.settings.sat?.default_volume.join(", ")}*/}
        {/*  </div>*/}
        {/*  <div className={styles.container_lowerBlock_settingsBlock_sunday}>Воскресенье</div>*/}
        {/*  <div className={styles.container_lowerBlock_settingsBlock_sunday_time}>*/}
        {/*    {data.settings.sun?.worktime.join(" - ")}*/}
        {/*  </div>*/}
        {/*  <div className={styles.container_lowerBlock_settingsBlock_sunday_volume}>*/}
        {/*    {data.settings.sun?.default_volume.join(", ")}*/}
        {/*  </div>*/}

        {/*  <div className={styles.container_lowerBlock_settingsBlock_customTime}>Кастомное время</div>*/}
        {/*  <div className={styles.container_lowerBlock_settingsBlock_customVolume}>Кастомная громкость</div>*/}

        {/*</div>*/}

        {/*settings*/}
        <div className={styles.container_lowerBlock}>


          {/*<div className={styles.container_lowerBlock_daysBlock}><h1>statistic</h1></div>*/}
        </div>
        {/*<button onClick={() => setEdit(true)}>Edit</button>*/}
      </div>
  );
}
