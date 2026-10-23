import { useMemo } from "react";
import { Autocomplete, TextField } from "@mui/material";
import { colorSuggestions } from "../../../utils/productOptions";

interface Props {
  value: string;
  onChange: (value: string) => void;
  usedColors: (string | null | undefined)[];  // colors already on products, offered as suggestions
}

// Pick a suggested color or type any other one (an empty field means no color)
export default function ColorField({ value, onChange, usedColors }: Props) {
  const options = useMemo(() => colorSuggestions(usedColors), [usedColors]);

  return (
    <Autocomplete
      freeSolo
      options={options}
      value={value || null}
      inputValue={value}
      onChange={(_, newValue) => onChange(newValue ?? "")}
      onInputChange={(_, newValue) => onChange(newValue)}
      sx={{ width: 180 }}
      renderInput={(params) => <TextField {...params} label="Color" placeholder="e.g. Black/White" />}
    />
  );
}
