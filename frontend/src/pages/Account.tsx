import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/useAuth";
import Navbar from "../components/Navbar";
import { updateEmail, updatePassword, deleteAccount, logoutEverywhere } from "../api/auth";
import { apiErrorMessage } from "../api/errors";

type FormMessage = { type: "success" | "error"; text: string } | null;

function Message({ message }: { message: FormMessage }) {
  if (!message) return null;
  return (
    <p className={`mb-4 text-sm ${message.type === "error" ? "text-red-600" : "text-green-700"}`}>
      {message.text}
    </p>
  );
}

export default function AccountPage() {
  const { user, refreshUser, logout } = useAuth();

  const [newEmail, setNewEmail] = useState("");
  const [emailPassword, setEmailPassword] = useState("");
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");

  const [emailMessage, setEmailMessage] = useState<FormMessage>(null);
  const [passwordMessage, setPasswordMessage] = useState<FormMessage>(null);
  const [deleteMessage, setDeleteMessage] = useState<FormMessage>(null);
  const [sessionMessage, setSessionMessage] = useState<FormMessage>(null);

  async function handleEmailUpdate(e: React.FormEvent) {
    e.preventDefault();

    try {
      await updateEmail(newEmail, emailPassword);
      setEmailMessage({ type: "success", text: "Email updated." });
      setNewEmail("");
      setEmailPassword("");
      await refreshUser();
    } catch (err) {
      setEmailMessage({ type: "error", text: apiErrorMessage(err, "Couldn't update your email.") });
    }
  }

  async function handlePasswordUpdate(e: React.FormEvent) {
    e.preventDefault();

    try {
      await updatePassword(oldPassword, newPassword);
      setPasswordMessage({ type: "success", text: "Password updated. Any other devices signed in to your account have been logged out." });
      setOldPassword("");
      setNewPassword("");
    } catch (err) {
      setPasswordMessage({ type: "error", text: apiErrorMessage(err, "Couldn't update your password.") });
    }
  }

  async function handleLogoutEverywhere() {
    if (!window.confirm("Log out on every device, including this one?")) return;

    try {
      await logoutEverywhere();
      window.location.href = "/login";
    } catch (err) {
      setSessionMessage({ type: "error", text: apiErrorMessage(err, "Couldn't log you out everywhere.") });
    }
  }

  async function handleDeleteAccount() {
    if (!window.confirm("Delete your account? This can't be undone.")) return;

    try {
      await deleteAccount();
      window.location.href = "/login";
    } catch (err) {
      setDeleteMessage({ type: "error", text: apiErrorMessage(err, "Couldn't delete your account.") });
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">

      {/* HEADER */}
      <Navbar className="bg-white shadow-xs" />

      {/* MAIN CONTENT */}
      <div className="w-full p-8 flex bg-white gap-10">

        {/* Account / User Navigation */}
        <div className="flex flex-col h-screen p-10 gap-4">

            <div className="flex flex-col items-end">
                <Link to="/account" className="text-xl tracking-widest">ACCOUNT</Link>
                <Link to="/" className="tracking-wider">SETTINGS</Link>
                {user?.is_admin === true ? (
                        <Link to="/admin">ADMIN</Link>
                    ) : (
                        <div>
                        </div>
                    )}
            </div>

            <div className="flex flex-col items-end">
                <Link to="/orders" className="text-xl tracking-widest">ORDERS</Link>
                <Link to="/orders" className="tracking-wider">TRACK</Link>
                <Link to="" className="tracking-wider">HISTORY</Link>
            </div>

        </div>

        <div className="flex flex-col justify-center w-screen">
          {/* Title */}
          <h1 className="text-5xl font-light text-center mb-12 tracking-tight">
            your account.
          </h1>

          {/* Profile Card */}
          <div className="bg-white shadow-xs p-8 rounded-2xl mb-12 border border-gray-200">
            <h2 className="text-xl font-medium mb-6 tracking-tight">Profile</h2>

            <div className="space-y-2 text-gray-700">

              <div className="flex flex-col border rounded-[10px] p-2">
                <p className="text-sm text-gray-400">Name</p>
                <p className="text-lg">{user?.first_name} {user?.last_name}</p>
              </div>

              <div className="flex flex-col border rounded-[10px] p-2">
                <p className="text-sm text-gray-400">Email</p>
                <p className="text-lg">{user?.email}</p>
              </div>

              <p>
                <strong>Member since:</strong>{" "}
                {user?.created_at
                  ? new Date(user.created_at).toLocaleDateString()
                  : "—"}
              </p>
            </div>

            {/* Logout Buttons */}
            <div className="mt-6 flex gap-6">
              <button
                onClick={logout}
                className="text-sm text-gray-500 underline hover:text-black transition"
              >
                Log out
              </button>
              {/* For a lost phone or a shared computer */}
              <button
                onClick={handleLogoutEverywhere}
                className="text-sm text-gray-500 underline hover:text-black transition"
              >
                Log out of all devices
              </button>
            </div>
            <div className="mt-4">
              <Message message={sessionMessage} />
            </div>
          </div>

          {/* Update Email */}
          <form
            onSubmit={handleEmailUpdate}
            className="bg-white shadow-xs p-8 rounded-2xl mb-12 border border-gray-200"
          >
            <h2 className="text-xl font-medium mb-6 tracking-tight">Update Email</h2>

            <Message message={emailMessage} />

            <input
              type="email"
              placeholder="New email"
              className="border p-3 rounded-sm w-full mb-4"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              required
            />

            <input
              type="password"
              placeholder="Current password"
              className="border p-3 rounded-sm w-full mb-4"
              value={emailPassword}
              onChange={(e) => setEmailPassword(e.target.value)}
              autoComplete="current-password"
              required
            />

            <button className="bg-black text-white px-6 py-2 rounded-full">
              Update Email
            </button>
          </form>

          {/* Update Password */}
          <form
            onSubmit={handlePasswordUpdate}
            className="bg-white shadow-xs p-8 rounded-2xl mb-12 border border-gray-200"
          >
            <h2 className="text-xl font-medium mb-6 tracking-tight">Update Password</h2>

            <Message message={passwordMessage} />

            <input
              type="password"
              placeholder="Old password"
              className="border p-3 rounded-sm w-full mb-4"
              value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)}
              autoComplete="current-password"
              required
            />

            <input
              type="password"
              placeholder="New password (at least 8 characters)"
              className="border p-3 rounded-sm w-full mb-4"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              autoComplete="new-password"
              minLength={8}
              required
            />

            <button className="bg-black text-white px-6 py-2 rounded-full">
              Update Password
            </button>
          </form>

          {/* Delete Account */}
          <div className="bg-white shadow-xs p-8 rounded-2xl text-center border border-gray-200">
            <Message message={deleteMessage} />
            <button
              onClick={handleDeleteAccount}
              className="bg-red-600 text-white px-6 py-2 rounded-full"
            >
              Delete Account
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
