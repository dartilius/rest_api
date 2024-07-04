"use client";

import { Select, SelectItem } from "@nextui-org/select";
import React from "react";

import { limitPages } from "../../../types/types/limitPages";

type SelectLimitProps = {
  label: string;
  placeholder: string;
  limitValue: number;
  setLimitValue: any;
};

const SelectLimit = (props: SelectLimitProps) => {
  const { label, placeholder, limitValue, setLimitValue } = props;
  const handleChange = (value: string) => {
    // Ensure the value is parsed to a number before setting it
    const parsedValue = Number(value);

    if (!isNaN(parsedValue)) {
      setLimitValue(parsedValue);
    } else {
      console.error("Invalid value selected:", value);
    }
  };

  return (
    <Select
      defaultSelectedKeys={[`${limitValue}`]}
      label={label}
      placeholder={placeholder}
      value={limitValue.toString()} // Ensure default value is a string
      onChange={(e) => handleChange(e.target.value)}
    >
      {limitPages.map((option) => (
        <SelectItem key={option.key} value={option.key}>
          {option.label}
        </SelectItem>
      ))}
    </Select>
  );
};

export default SelectLimit;
