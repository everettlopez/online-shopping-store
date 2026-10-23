import { useEffect, useState } from "react";
import { FormControlLabel, Switch, TextField } from "@mui/material";
import AdminNav from "../../components/admin/AdminNav";
import ConfirmDeleteModal from "../../components/admin/ConfirmDeleteModal";
import AdminSnackbar, { type AdminNotice } from "../../components/admin/AdminSnackbar";
import AdminUserEditModal from "../../components/admin/users/AdminUserEditModal";
import { createUser, deleteUser, getUsers, updateUser, type AdminUser, type AdminUserInput } from "../../api/admin";
import { apiErrorMessage } from "../../api/errors";


export default function AdminUsers() {

    const [users, setUsers] = useState<AdminUser[]>([]);
    const [notice, setNotice] = useState<AdminNotice>(null);
    const [editingUser, setEditingUser] = useState<AdminUser | null>(null);
    const [pendingDelete, setPendingDelete] = useState<AdminUser | null>(null);

    // Create form
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [firstName, setFirstName] = useState("");
    const [lastName, setLastName] = useState("");
    const [isAdmin, setIsAdmin] = useState(false);

    async function fetchUsers() {
        try {
            setUsers(await getUsers());
        }
        catch (err) {
            setNotice({ severity: "error", message: apiErrorMessage(err, "Failed to load users") });
        }
    }

    useEffect(() => {
        getUsers().then(setUsers, (err) => setNotice({ severity: "error", message: apiErrorMessage(err, "Failed to load users") }));
    }, []);

    function resetCreateForm() {
        setEmail("");
        setPassword("");
        setFirstName("");
        setLastName("");
        setIsAdmin(false);
    }

    async function handleCreate() {
        try {
            await createUser({ email: email.trim(), password, first_name: firstName.trim(), last_name: lastName.trim(), is_admin: isAdmin });
            resetCreateForm();
            setNotice({ severity: "success", message: "User created" });
            fetchUsers();
        }
        catch (err) {
            setNotice({ severity: "error", message: apiErrorMessage(err, "Failed to create user") });
        }
    }

    async function handleUpdate(userId: number, data: Partial<AdminUserInput>) {
        try {
            await updateUser(userId, data);
            setEditingUser(null);
            setNotice({ severity: "success", message: "User updated" });
            fetchUsers();
        }
        catch (err) {
            setNotice({ severity: "error", message: apiErrorMessage(err, "Failed to update user") });
        }
    }

    async function handleDelete() {
        if (!pendingDelete) return;

        try {
            await deleteUser(pendingDelete.user_id);
            setNotice({ severity: "success", message: "User deleted" });
            fetchUsers();
        }
        catch (err) {
            setNotice({ severity: "error", message: apiErrorMessage(err, "Failed to delete user") });
        }
        finally {
            setPendingDelete(null);
        }
    }


    return (
        <>
        <AdminNav />

        <div className="p-10 flex flex-col gap-6">

            {/* Create User */}
            <div className="flex flex-col gap-3">
                <h1 className="text-4xl tracking-wider">CREATE NEW USER</h1>
                <div className="flex flex-wrap gap-2 items-center border rounded-lg p-2">
                    <TextField required label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)}/>
                    <TextField required label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)}/>
                    <TextField required label="First Name" value={firstName} onChange={(e) => setFirstName(e.target.value)}/>
                    <TextField required label="Last Name" value={lastName} onChange={(e) => setLastName(e.target.value)}/>
                    <FormControlLabel label="Admin" control={<Switch checked={isAdmin} onChange={(e) => setIsAdmin(e.target.checked)}/>}/>
                    <button disabled={!email.trim() || !password || !firstName.trim() || !lastName.trim()} onClick={handleCreate} className="border rounded-full px-5 py-1 disabled:bg-gray-100 disabled:text-gray-400">Create</button>
                </div>
            </div>

            {/* Users Table */}
            <div className="py-4 border rounded-lg bg-white shadow-sm flex flex-col divide-y">

                <div className="grid grid-cols-6 gap-4 text-sm font-semibold text-gray-500 border-b pb-2">
                    <div className="text-center">First Name</div>
                    <div className="text-center">Last Name</div>
                    <div className="text-center">Created At</div>
                    <div className="text-center">Email</div>
                    <div className="text-center">Admin</div>
                    <div className="text-center">Actions</div>
                </div>

                {users.map(user => (
                <div key={user.user_id} className="grid grid-cols-6 gap-4 py-2 items-center">
                    <div className="text-center">{user.first_name}</div>
                    <div className="text-center">{user.last_name}</div>
                    <div className="text-center">{new Date(user.created_at).toLocaleString()}</div>
                    <div className="text-center">{user.email}</div>
                    <div className="text-center">{user.is_admin ? "Yes" : "No"}</div>

                    <div className="flex justify-center gap-2">
                        <button onClick={() => setEditingUser(user)} className="border rounded-[10px] px-8 py-1 hover:bg-gray-300">Update</button>
                        <button onClick={() => setPendingDelete(user)} className="border rounded-[10px] px-8 py-1 bg-red-500 text-white hover:bg-red-600">Delete</button>
                    </div>
                </div>
                ))}

            </div>
        </div>

        <AdminUserEditModal
            user={editingUser}
            onClose={() => setEditingUser(null)}
            onSave={handleUpdate}
        />

        <ConfirmDeleteModal
            open={pendingDelete !== null}
            message={`Are you sure you want to delete ${pendingDelete?.first_name} ${pendingDelete?.last_name} (${pendingDelete?.email})?`}
            onClose={() => setPendingDelete(null)}
            onConfirm={handleDelete}
        />

        <AdminSnackbar notice={notice} onClose={() => setNotice(null)} />
        </>
    );
}
