import { Link } from "react-router-dom";   // ← FIXED: Link imported
import { useEffect, useState } from "react";


export default function AdminUsers() {

    type User = {
        user_id: number;
        email: string;
        first_name: string;
        last_name: string;
        created_at: string;
        is_admin: boolean;
    };


    const handleEditUser = (user: User) => {
        console.log("Edit user:", user);
    // later: open modal / navigate to edit page
    };

    const handleDeleteUser = (user: User) => {
        console.log("Delete user:", user);
    // later: call API, then update state
    };

    const [users, setUsers] = useState<User[]>([]);

    useEffect(() => {
    const fetchUsers = async () => {
        try {
        const res = await fetch("http://127.0.0.1:8000/api/admin/users", {
            credentials: "include", // important for admin auth
        });

        if (!res.ok) {
            console.error("Failed to fetch users");
            return;
        }

        const data: User[] = await res.json();
        setUsers(data);
        } catch (err) {
        console.error("Error fetching users:", err);
        }
    };

    fetchUsers();
    }, []);




    return (
        <>
        {/* Header */}
        <div className="relative flex flex-col justify-center items-center gap-4 p-5">
            <a href="/"><h1 className="text-6xl">KILLJOY</h1></a>

            <nav className="flex gap-12">
            <Link to="/admin/products">
                <p className="text-base font-normal tracking-widest">PRODUCTS</p>
            </Link>
            <Link to="/admin/categories">
                <p className="text-base font-normal tracking-widest">CATEGORIES</p>
            </Link>
            <Link to="/admin/users">
                <p className="text-base font-normal tracking-widest">USERS</p>
            </Link>
            <Link to="/admin/orders">
                <p className="text-base font-normal tracking-widest">ORDERS</p>
            </Link>
            </nav>
        </div>

        {/* Users Section */}
        <div className="p-6 border rounded-lg bg-white shadow-sm flex flex-col gap-4">

        {/* Header */}
        <div className="grid grid-cols-5 gap-4 text-sm font-semibold text-gray-500 border-b pb-2">
            <div className="text-center">First Name</div>
            <div className="text-center">Last Name</div>
            <div className="text-center">Created At</div>
            <div className="text-center">Email</div>
            <div className="text-center">Actions</div>
        </div>

        {/* User Rows */}
        {users.map(user => (
        <div key={user.user_id} className="grid grid-cols-5 gap-4 py-2">
            <div className="text-center">{user.first_name}</div>
            <div className="text-center">{user.last_name}</div>
            <div className="text-center">
            {new Date(user.created_at).toLocaleString()}
            </div>
            <div className="text-center">{user.email}</div>

            {/* Actions Buttons */}
            <div className="flex justify-center gap-2">
                <button onClick={() => handleEditUser(user)} className="border rounded-[10px] px-8 py-1 hover:bg-gray-300">Update</button>
                <button onClick={() => handleDeleteUser(user)} className="border rounded-[10px] px-8 py-1 bg-red-500 text-white hover:bg-red-600">Delete</button>
            </div>
        </div>
        ))}



        </div>

        </>
    );
}