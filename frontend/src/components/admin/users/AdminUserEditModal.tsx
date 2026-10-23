import { useState } from "react";
import Modal from "@mui/material/Modal";
import { FormControlLabel, Switch, TextField } from "@mui/material";
import type { AdminUser, AdminUserInput } from "../../../api/admin";

interface Props {
  user: AdminUser | null;
  onClose: () => void;
  onSave: (userId: number, data: Partial<AdminUserInput>) => void;
}

// A fresh form for each user opened, prefilled from that user
export default function AdminUserEditModal(props: Props) {
  if (!props.user) return null;
  return <UserForm key={props.user.user_id} {...props} user={props.user} />;
}

function UserForm({ user, onClose, onSave }: Props & { user: AdminUser }) {
  const [email, setEmail] = useState(user.email);
  const [firstName, setFirstName] = useState(user.first_name);
  const [lastName, setLastName] = useState(user.last_name);
  const [isAdmin, setIsAdmin] = useState(user.is_admin);
  const [password, setPassword] = useState("");

  function handleSave() {

    const data: Partial<AdminUserInput> = {
      email: email.trim(),
      first_name: firstName.trim(),
      last_name: lastName.trim(),
      is_admin: isAdmin,
    };

    // Blank password leaves the current one unchanged
    if (password) data.password = password;

    onSave(user.user_id, data);
  }

  return (
    <Modal open onClose={onClose}>
      <div className="bg-white p-6 rounded-lg shadow-xl w-[500px] max-w-[calc(100vw-32px)] mx-auto mt-[15vh] flex flex-col gap-4">
        <h2 className="text-2xl tracking-wider">EDIT USER</h2>

        <TextField required label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)}/>
        <div className="flex gap-2">
          <TextField required label="First Name" className="flex-1" value={firstName} onChange={(e) => setFirstName(e.target.value)}/>
          <TextField required label="Last Name" className="flex-1" value={lastName} onChange={(e) => setLastName(e.target.value)}/>
        </div>
        <TextField label="New Password" type="password" helperText="Leave blank to keep the current password" value={password} onChange={(e) => setPassword(e.target.value)}/>
        <FormControlLabel label="Admin" control={<Switch checked={isAdmin} onChange={(e) => setIsAdmin(e.target.checked)}/>}/>

        <div className="flex justify-between">
          <button onClick={onClose} className="border px-4 py-2 rounded-full">Cancel</button>
          <button disabled={!email.trim() || !firstName.trim() || !lastName.trim()} onClick={handleSave} className="bg-green-300 px-4 py-2 rounded-full disabled:bg-gray-100 disabled:text-gray-400">Save</button>
        </div>
      </div>
    </Modal>
  );
}
