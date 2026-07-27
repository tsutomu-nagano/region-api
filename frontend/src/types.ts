export type MunicipalityRef = {
  code: string | null;
  name: string;
  code_inferred: boolean;
};

export type MergerEvent = {
  type:
    | "merge_new"
    | "absorption"
    | "new_establishment"
    | "split"
    | "city_status"
    | "town_status"
    | "rename"
    | "designated_city"
    | "core_city"
    | "special_city";
  label: string;
  source_municipalities: MunicipalityRef[];
  target_municipalities: MunicipalityRef[];
};

export type Merger = {
  id: number;
  code: string;
  prefecture_code: string;
  prefecture_name: string;
  district_name: string | null;
  district_kana: string | null;
  municipality_name: string | null;
  municipality_kana: string | null;
  effective_date: string | null;
  reason: string;
  reason_events: MergerEvent[];
};
