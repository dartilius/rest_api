"use client";
import { Input } from "@nextui-org/react";
import React from "react";

type SearchProps = {
  searchValue: string;
  onSearchChange: any;
  onSearchSubmit: any;
  label: string;
  placeholder: string;
};

const Search = (props: SearchProps) => {
  const { searchValue, onSearchChange, onSearchSubmit, label, placeholder } = props;
  const handleKeyDown = (event: { key: string }) => {
    if (event.key === "Enter") {
      onSearchSubmit();
    }
  };

  return (
    <div className="flex w-full flex-wrap md:flex-nowrap gap-4">
      <Input
        label={label}
        placeholder={placeholder}
        type="text"
        value={searchValue}
        onChange={onSearchChange}
        onKeyDown={handleKeyDown}
      />
    </div>
  );
};

export default Search;
