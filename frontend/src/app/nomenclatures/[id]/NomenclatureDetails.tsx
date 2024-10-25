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
import {MouseEvent, useEffect, useMemo, useState} from "react";

import DeletingModal from "../../../components/ui/DeletingModal";

import TranscriptData from "./components/TranscriptData";
import EditingModal from "./components/EditingModal";

import styles from './NomenclatureDetails.module.scss'

import {
  DaySettings, HwInfo,
  NomenclatureInterface,
} from "@/src/types/interface/nomenclature.interface";
import Loader from "@/src/components/ui/Loader";
import { toastSuccess } from "@/src/utils/toast-success";
import { toastError } from "@/src/utils/toast-error";
import {
  useDeleteNomenclatureQuery,
  useNomenclatureAdQuery,
  useNomenclatureQuery
} from "@/src/hooks/nomenclatures/useNomenclatureQuery";
import useIdFromParams from "@/src/hooks/useIdFromParams";
import CustomTextarea from "@/src/app/nomenclatures/[id]/components/CustomTextArea";
import {convertStatus} from "@/src/types/types/checkStatus";
import {convertZone, timezonesArray} from "@/src/types/types/timezone";
import nomenclaturesService from "@/src/services/nomenclatures/nomenclatures.service";
import {AxisOptions, Chart} from "react-charts";

type Props = {
  id: string | undefined;
  // data: NomenclatureInterface | undefined;
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

// type MyDatum = { date: Date, stars: number }
//
// function MyChart() {
//   const data = [
//     {
//       label: 'React Charts',
//       data: [
//         {
//           date: 50,
//           stars: 234,
//         },
//       ],
//     },
//     {
//       label: 'React Charts 2',
//       data: [
//         {
//           date: 110,
//           stars: 23,
//         },
//       ],
//     },
//     {
//       label: 'React Charts 3',
//       data: [
//         {
//           date: 1000,
//           stars: 265,
//         },
//       ],
//     },
//   ]
//
//   const primaryAxis = useMemo(
//       (): AxisOptions<MyDatum> => ({
//         getValue: datum => datum.date,
//       }),
//       []
//   )
//
//   const secondaryAxes = useMemo(
//       (): AxisOptions<MyDatum>[] => [
//         {
//           getValue: datum => datum.stars,
//         },
//       ],
//       []
//   )
//
//   return (
//       <Chart
//           options={{
//             data,
//             primaryAxis,
//             secondaryAxes,
//
//           }}
//       />
//   )
// }


export default function NomenclatureDetails(props: Props) {
  // const { data } = props;
  const id = useIdFromParams();
  const [edit, setEdit] = useState<boolean>(false);
  const [openEditingModal, setOpenEditingModal] = useState<boolean>(false);
  const [openDeletingModal, setOpenDeletingModal] = useState<boolean>(false);
  const [fetchAdStats, setFetchAdStats] = useState(false);
  const [isMounted, setIsMounted] = useState(true);

  const { mutateAsync: deleteNomenclature, isSuccess: isDeleteSuccess, error: deleteError, isError: isDeleteError } = useDeleteNomenclatureQuery();

  const {data} = useNomenclatureQuery(id)

  useEffect(() => {
    if (isDeleteSuccess) {
      toastSuccess("Номенклатура успешно удалена");
      const timeoutId = setTimeout(() => {
        window.location.replace("/nomenclatures");
      }, 2500);
      return () => clearTimeout(timeoutId);
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

  const hwInfo = data.hw_info

  const {adStat} = useNomenclatureAdQuery(id)
  console.log(adStat)


  return (
      // <MyChart />
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

          <div className={styles.container_lowerBlock_settingsBlock}>
            {/*{renderSettingsTable(data.settings)}*/}
            <div className={styles.container_lowerBlock_settingsBlock_start}>Время работы</div>
            <div className={styles.container_lowerBlock_settingsBlock_volume}>Стандартная громкость</div>
            <div className={styles.container_lowerBlock_settingsBlock_monday}>Понедельник</div>
            <div
                className={styles.container_lowerBlock_settingsBlock_monday_time}>{data.settings.mon?.worktime}</div>
            <div
                className={styles.container_lowerBlock_settingsBlock_monday_volume}>{data.settings.mon?.default_volume.join(', ')}</div>
            <div className={styles.container_lowerBlock_settingsBlock_tuesday}>Вторник</div>
            <div className={styles.container_lowerBlock_settingsBlock_tuesday_time}>
              {data.settings.tue?.worktime}
            </div>
            <div className={styles.container_lowerBlock_settingsBlock_tuesday_volume}>
              {data.settings.tue?.default_volume.join(", ")}
            </div>
            <div className={styles.container_lowerBlock_settingsBlock_wednesday}>Среда</div>
            <div className={styles.container_lowerBlock_settingsBlock_wednesday_time}>
              {data.settings.wed?.worktime}
            </div>
            <div className={styles.container_lowerBlock_settingsBlock_wednesday_volume}>
              {data.settings.wed?.default_volume.join(", ")}
            </div>
            <div className={styles.container_lowerBlock_settingsBlock_thusday}>Четверг</div>
            <div className={styles.container_lowerBlock_settingsBlock_thusday_time}>
              {data.settings.thu?.worktime}
            </div>
            <div className={styles.container_lowerBlock_settingsBlock_thusday_volume}>
              {data.settings.thu?.default_volume.join(", ")}
            </div>
            <div className={styles.container_lowerBlock_settingsBlock_friday}>Пятница</div>
            <div className={styles.container_lowerBlock_settingsBlock_friday_time}>
              {data.settings.fri?.worktime}
            </div>
            <div className={styles.container_lowerBlock_settingsBlock_friday_volume}>
              {data.settings.fri?.default_volume.join(", ")}
            </div>
            <div className={styles.container_lowerBlock_settingsBlock_saturday}>Суббота</div>
            <div className={styles.container_lowerBlock_settingsBlock_saturday_time}>
              {data.settings.sat?.worktime}
            </div>
            <div className={styles.container_lowerBlock_settingsBlock_saturday_volume}>
              {data.settings.sat?.default_volume.join(", ")}
            </div>
            <div className={styles.container_lowerBlock_settingsBlock_sunday}>Воскресенье</div>
            <div className={styles.container_lowerBlock_settingsBlock_sunday_time}>
              {data.settings.sun?.worktime}
            </div>
            <div className={styles.container_lowerBlock_settingsBlock_sunday_volume}>
              {data.settings.sun?.default_volume.join(", ")}
            </div>
          </div>
        </div>


        {/*settings*/}
        <div className={styles.container_lowerBlock}>
          <div className={styles.container_upperBlock_hwInfo}>
            <h1 className={styles.container_upperBlock_mainInfo_name} style={{justifyContent: 'flex-start'}}>Информация о железе:</h1>
            {data.hw_info ? (
                <div>
                  <div>
                    <p><i>Модель</i>: {hwInfo.model}</p>
                    <p><i>Ревизия</i>: {hwInfo.revision}</p>
                    <p><i>Серийный номер</i>: {hwInfo.serial_number}</p>
                  </div>
                  <div>
                    <h4>Аудио девайсы</h4>
                    <ul>
                      {hwInfo.audiodevices.map((device, index) => (
                          <li key={index}>
                            <i>Card {device.card}</i>: {device.name}
                          </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <p><strong>Настройки сети</strong></p>
                    <ul>
                      {hwInfo.interfaces.map((networkInterface, index) => (
                          <li key={index}>
                            <i>Interface</i>: {networkInterface.iface} <br/>
                            <i>MAC</i>: {networkInterface.mac} <i>IP</i>: <span>{networkInterface.ip ? networkInterface.ip : 'N/A'}</span>
                          </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4>SD карта</h4>
                    <p><i>Manufacturer ID</i>: {hwInfo.sd_card_data.manf_id}</p>
                    <p><i>SD Card Name</i>: {hwInfo.sd_card_data.name}</p>
                  </div>
                </div>
            ) : (
                <div>
                  <p><strong>Проебалось куда-то</strong></p>
                </div>
            )}
          </div>

          {/*<div className={styles.container_lowerBlock_daysBlock}><h1>statistic</h1></div>*/}
        </div>
        {/*<button onClick={() => setEdit(true)}>Edit</button>*/}
      </div>
  );
}
