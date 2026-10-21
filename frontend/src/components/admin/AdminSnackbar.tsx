import Snackbar from "@mui/material/Snackbar";
import Alert from "@mui/material/Alert";

export type AdminNotice = { severity: "success" | "error"; message: string } | null;

interface Props {
  notice: AdminNotice;
  onClose: () => void;
}

export default function AdminSnackbar({ notice, onClose }: Props) {
  return (
    <Snackbar
      open={notice !== null}
      autoHideDuration={4000}
      onClose={(_event, reason) => { if (reason !== "clickaway") onClose(); }}
      anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
    >
      <Alert onClose={onClose} severity={notice?.severity ?? "success"} variant="filled" sx={{ width: "100%" }}>
        {notice?.message}
      </Alert>
    </Snackbar>
  );
}
