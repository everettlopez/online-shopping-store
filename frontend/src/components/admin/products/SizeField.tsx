import { Autocomplete, TextField } from "@mui/material";
import { PRESET_SIZES, sizeGroup } from "../../../utils/productOptions";

interface Props {
  value: string;
  onChange: (value: string) => void;
}

// Pick a preset size or type any other one (an empty field means no size)
export default function SizeField({ value, onChange }: Props) {
  return (
    <Autocomplete
      freeSolo
      options={PRESET_SIZES}
      groupBy={sizeGroup}
      value={value || null}
      inputValue={value}
      onChange={(_, newValue) => onChange(newValue ?? "")}
      onInputChange={(_, newValue) => onChange(newValue)}
      sx={{ width: 180 }}
      renderInput={(params) => <TextField {...params} label="Size" placeholder="e.g. M, 32x30" />}
    />
  );
}
