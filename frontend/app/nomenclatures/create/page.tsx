"use client";

import React from "react";

import styles from "./NomenclatureCreate.module.scss";

import { NomenclatureCreateInterface } from "../../../types/interface/nomenclature.interface";

interface NomenclatureCreateProps {
  data: NomenclatureCreateInterface;
}

export default function NomenclatureCreate() {
  // const [formData, setFormData] = useState<NomenclatureCreateInterface>({
  //   name: data?.name || "",
  //   description: data?.description || "",
  //   timezone: data?.timezone || "",
  //   settings: {}, // Начальные настройки пусты
  // });

  // const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
  //   const { name, value } = event.target;

  //   setFormData((prevData) => ({
  //     ...prevData,
  //     [name]: value,
  //   }));
  // };

  // const handleTimeZoneChange = (value: string) => {
  //   setFormData((prevData) => ({
  //     ...prevData,
  //     timezone: value,
  //   }));
  // };

  // const handleSettingChange = (day: Day, setting: keyof SettingsInterface, value: string) => {
  //     setFormData(prevData => {
  //         const currentSettings = prevData.settings[day];
  //         const updatedDaySettings: SettingsInterface = typeof currentSettings === 'object' && currentSettings !== null ? currentSettings : {}; // Явное определение типа

  //         updatedDaySettings[setting] = value;

  //         return {
  //             ...prevData,
  //             settings: {
  //                 ...prevData.settings,
  //                 [day]: updatedDaySettings
  //             }
  //         };
  //     });
  // };

  // const handleSubmit = () => {
  //   // Ваша логика сохранения данных
  //   console.log("Form Data:", formData);
  // };

  return (
    <div className={styles.container}>
      надо переписать
      {/* <Form className={styles.form} layout="vertical" onFinish={handleSubmit}>
        <Form.Item label="Название" name="name">
          <Input
            name="name"
            value={formData.name}
            onChange={handleInputChange}
          />
        </Form.Item>
        <Form.Item label="Описание" name="description">
          <Input
            name="description"
            value={formData.description}
            onChange={handleInputChange}
          />
        </Form.Item>
        <Form.Item label="Timezone" name="timezone">
          <Select
            placeholder="Select timezone"
            style={{ width: "100%" }}
            value={formData.timezone}
            onChange={handleTimeZoneChange}
          >
            {timezonesArray.map((timezone) => (
              <Option key={timezone.value} value={timezone.value}>
                {timezone.label}
              </Option>
            ))}
          </Select>
        </Form.Item>
        Настройки:
        {Object.keys(formData.settings).map((day: keyof SettingsInterface) => (
          <div key={day}>
            <label>{day}:</label>
            <Input
                            value={formData.settings[day]?.worktime || ''}
                            onChange={(e) => handleSettingChange(day, 'worktime', e.target.value)}
                            style={{ marginBottom: '8px' }}
                            placeholder="Worktime"
                        />
                        <Input
                            value={formData.settings[day]?.default_volume || ''}
                            onChange={(e) => handleSettingChange(day, 'default_volume', e.target.value)}
                            style={{ marginBottom: '8px' }}
                            placeholder="Default Volume"
                        />
          </div>
        ))}

        <Button htmlType="submit" type="primary">
          Сохранить
        </Button>
      </Form> */}
    </div>
  );
}
