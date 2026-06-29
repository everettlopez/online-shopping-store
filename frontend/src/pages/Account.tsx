import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function AccountPage() {
  const { user, refreshUser, logout } = useAuth();

  const [newEmail, setNewEmail] = useState("");
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");

  async function handleEmailUpdate(e: React.FormEvent) {
    e.preventDefault();

    await fetch("/api/auth/me/email", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: newEmail }),
    });

    refreshUser();
  }

  async function handlePasswordUpdate(e: React.FormEvent) {
    e.preventDefault();

    const formData = new FormData();
    formData.append("old_password", oldPassword);
    formData.append("new_password", newPassword);

    await fetch("/api/auth/me/password", {
      method: "PUT",
      body: formData,
    });
  }

  async function handleDeleteAccount() {
    await fetch("/api/auth/me", { method: "DELETE" });
    window.location.href = "/login";
  }

  return (
    <div className="min-h-screen bg-gray-50">

      {/* HEADER */}
      <header className="relative flex flex-col justify-center items-center gap-4 p-5 bg-white shadow-sm">

        {/* Right-side icons */}
        <div className="absolute right-5 top-5 flex items-center gap-6 text-2xl">
          <Link to="/account" className="hover:text-gray-600 transition">
            <i className="fa-regular fa-user"></i>
          </Link>

          <Link to="/cart" className="hover:text-gray-600 transition">
            <i className="fa-solid fa-bag-shopping"></i>
          </Link>
        </div>

        {/* Logo */}
        <Link to="/">
          <h1 className="text-6xl tracking-tight font-light">KILLJOY</h1>
        </Link>

        {/* Navigation */}
        <nav className="flex gap-12 text-sm tracking-widest text-gray-700">
          <Link to="/"><p>EVENTS</p></Link>
          <Link to="/products?category=1"><p>NEW ARRIVALS</p></Link>
          <Link to="/products?category=2"><p>WOMEN</p></Link>
          <Link to="/products?category=3"><p>MEN</p></Link>
          <Link to="/products?category=4"><p>BRANDS</p></Link>
          <Link to="/products?category=5"><p>ACCESSORIES</p></Link>
          <Link to="/products?category=6"><p>JEWELERY</p></Link>
        </nav>
      </header>

      {/* MAIN CONTENT */}
      <div className="max-w-3xl mx-auto p-10">

        {/* Title */}
        <h1 className="text-5xl font-light text-center mb-12 tracking-tight">
          your account.
        </h1>

        {/* Profile Card */}
        <div className="bg-white shadow-sm p-8 rounded-2xl mb-12 border border-gray-200">
          <h2 className="text-xl font-medium mb-6 tracking-tight">Profile</h2>

          <div className="space-y-2 text-gray-700">
            <p><strong>Name:</strong> {user?.first_name} {user?.last_name}</p>
            <p><strong>Email:</strong> {user?.email}</p>
            <p>
              <strong>Member since:</strong>{" "}
              {user?.created_at
                ? new Date(user.created_at).toLocaleDateString()
                : "—"}
            </p>
          </div>

          {/* Logout Button */}
          <button
            onClick={logout}
            className="mt-6 text-sm text-gray-500 underline hover:text-black transition"
          >
            Log out
          </button>
        </div>

        {/* Update Email */}
        <form
          onSubmit={handleEmailUpdate}
          className="bg-white shadow-sm p-8 rounded-2xl mb-12 border border-gray-200"
        >
          <h2 className="text-xl font-medium mb-6 tracking-tight">Update Email</h2>

          <input
            type="email"
            placeholder="New email"
            className="border p-3 rounded w-full mb-4"
            value={newEmail}
            onChange={(e) => setNewEmail(e.target.value)}
          />

          <button className="bg-black text-white px-6 py-2 rounded-full">
            Update Email
          </button>
        </form>

        {/* Update Password */}
        <form
          onSubmit={handlePasswordUpdate}
          className="bg-white shadow-sm p-8 rounded-2xl mb-12 border border-gray-200"
        >
          <h2 className="text-xl font-medium mb-6 tracking-tight">Update Password</h2>

          <input
            type="password"
            placeholder="Old password"
            className="border p-3 rounded w-full mb-4"
            value={oldPassword}
            onChange={(e) => setOldPassword(e.target.value)}
          />

          <input
            type="password"
            placeholder="New password"
            className="border p-3 rounded w-full mb-4"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />

          <button className="bg-black text-white px-6 py-2 rounded-full">
            Update Password
          </button>
        </form>

        {/* Delete Account */}
        <div className="bg-white shadow-sm p-8 rounded-2xl text-center border border-gray-200">
          <button
            onClick={handleDeleteAccount}
            className="bg-red-600 text-white px-6 py-2 rounded-full"
          >
            Delete Account
          </button>
        </div>

      </div>
    </div>
  );
}
