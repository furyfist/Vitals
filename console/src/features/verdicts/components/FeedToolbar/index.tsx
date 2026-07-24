import { LayoutList, Rows } from "lucide-react";
import type React from "react";
import Dropdown from "@/components/Dropdown";
import IconButton from "@/components/IconButton";

export interface FeedToolbarProps {
  sort: "newest" | "oldest" | "sigma";
  onSortChange: (sort: "newest" | "oldest" | "sigma") => void;
  density: "comfortable" | "compact";
  onDensityChange: (density: "comfortable" | "compact") => void;
  services?: string[];
  selectedService?: string;
  onServiceChange?: (service?: string) => void;
  className?: string;
}

export const FeedToolbar: React.FC<FeedToolbarProps> = ({
  sort,
  onSortChange,
  density,
  onDensityChange,
  services = [],
  selectedService,
  onServiceChange,
  className = "",
}) => {
  const sortOptions = [
    { value: "newest", label: "Newest first" },
    { value: "oldest", label: "Oldest first" },
    { value: "sigma", label: "Highest sigma" },
  ];

  const serviceOptions = [
    { value: "", label: "All services" },
    ...services.map((s) => ({ value: s, label: s })),
  ];

  return (
    <div
      className={className}
      style={{
        display: "flex",
        alignItems: "center",
        gap: "12px",
      }}
    >
      {services.length > 0 && onServiceChange && (
        <Dropdown
          options={serviceOptions}
          value={selectedService || ""}
          onChange={(val) => onServiceChange(val || undefined)}
          placeholder="All services"
          ariaLabel="Filter by service"
        />
      )}

      <Dropdown
        options={sortOptions}
        value={sort}
        onChange={(val) => onSortChange(val as "newest" | "oldest" | "sigma")}
        ariaLabel="Sort verdicts"
      />

      <div style={{ display: "flex", alignItems: "center", gap: "2px" }}>
        <IconButton
          icon={<LayoutList size={16} aria-hidden="true" />}
          aria-label="Comfortable density"
          variant={density === "comfortable" ? "secondary" : "ghost"}
          size="sm"
          onClick={() => onDensityChange("comfortable")}
        />
        <IconButton
          icon={<Rows size={16} aria-hidden="true" />}
          aria-label="Compact density"
          variant={density === "compact" ? "secondary" : "ghost"}
          size="sm"
          onClick={() => onDensityChange("compact")}
        />
      </div>
    </div>
  );
};

export default FeedToolbar;
