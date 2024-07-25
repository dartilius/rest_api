import { Select, SelectItem, Pagination } from "@nextui-org/react";

import { limitPages } from "@/src/types/types/limitPages";

type PaginationComponentProps = {
  page: number;
  total: number;
  limit: number;
  onPageChange: (newPage: number) => void;
  onLimitChange: (newLimit: number) => void;
};

export const PaginationComponent = ({
  page,
  total,
  limit,
  onPageChange,
  onLimitChange,
}: PaginationComponentProps) => {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        gap: 24,
        alignItems: "center",
      }}
    >
      <Pagination
        isCompact
        showControls
        showShadow
        color="secondary"
        page={page}
        total={total}
        onChange={onPageChange}
      />
      <div style={{ maxWidth: 120, width: 100 }}>
        <Select
          defaultSelectedKeys={[`${limit}`]}
          value={limit.toString()}
          onChange={(e) => onLimitChange(parseInt(e.target.value))}
        >
          {limitPages.map((option) => (
            <SelectItem key={option.key} value={option.key}>
              {option.label}
            </SelectItem>
          ))}
        </Select>
      </div>
    </div>
  );
};
